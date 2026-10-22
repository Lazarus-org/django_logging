"""Bounded best-effort SMTP notification delivery.

Each process may have only a limited number of in-flight notifications.
When saturated, a notification is rejected rather than creating an
unbounded number of threads. This is deliberately NOT a durable queue or
delivery guarantee.

"""

import logging
import os
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

_MAX_CONCURRENT_DEFAULT = 4
_TIMEOUT_DEFAULT = 10
_limiter_lock = threading.Lock()
_limiter_pid = None
_limiter_capacity = None
_limiter = None


def _options() -> tuple[int, int]:
    """Read the existing DJANGO_LOGGING/LOG_EMAIL_NOTIFIER settings."""
    # Exact integers reject bools and numeric subclasses for resource limits.
    # pylint: disable=unidiomatic-typecheck
    conf = getattr(settings, "DJANGO_LOGGING", {})
    raw = conf.get("LOG_EMAIL_NOTIFIER", {}) if isinstance(conf, dict) else {}
    if not isinstance(raw, dict):
        raw = {}
    concurrency = raw.get("MAX_CONCURRENT", _MAX_CONCURRENT_DEFAULT)
    timeout = raw.get("SMTP_TIMEOUT", _TIMEOUT_DEFAULT)
    if type(concurrency) is not int or not 1 <= concurrency <= 64:
        raise ValueError(
            "LOG_EMAIL_NOTIFIER.MAX_CONCURRENT must be an integer from 1 to 64"
        )
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise ValueError(
            "LOG_EMAIL_NOTIFIER.SMTP_TIMEOUT must be an integer from 1 to 120"
        )
    return concurrency, timeout


def _semaphore(capacity: int) -> threading.BoundedSemaphore:
    """Limit work per process, reinitializing a lock inherited after fork."""
    global _limiter, _limiter_pid, _limiter_capacity  # pylint: disable=global-statement
    with _limiter_lock:
        pid = os.getpid()
        if _limiter_pid != pid or _limiter is None or _limiter_capacity != capacity:
            _limiter = threading.BoundedSemaphore(capacity)
            _limiter_pid = pid
            _limiter_capacity = capacity
        return _limiter


def _after_fork() -> None:
    """Discard inherited synchronization state in a pre-fork worker."""
    global _limiter_lock, _limiter, _limiter_pid, _limiter_capacity  # pylint: disable=global-statement
    _limiter_lock = threading.Lock()
    _limiter = None
    _limiter_pid = os.getpid()
    _limiter_capacity = None


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_after_fork)


def send_email_async(
    subject: str,
    body: str,
    recipient_list: List[str],
    event: Optional[threading.Event] = None,
) -> bool:
    """Attempt best-effort delivery, returning False if the worker is
    saturated.

    The event is set on both completion and rejection. Never block
    request threads while waiting for SMTP or for a capacity slot.

    """
    capacity, timeout = _options()
    slot = _semaphore(capacity)
    # A context manager would block; the worker must release this slot.
    if not slot.acquire(blocking=False):  # pylint: disable=consider-using-with
        logger.warning("Email notifier at capacity; dropping notification")
        if event is not None:
            event.set()
        return False

    def send_email() -> None:
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.DEFAULT_FROM_EMAIL
            msg["To"] = ", ".join(recipient_list)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            # A finite timeout bounds blocked SMTP network operations. STARTTLS
            # and login retain the existing notifier behavior.
            server = SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=timeout)
            try:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(
                    settings.DEFAULT_FROM_EMAIL, recipient_list, msg.as_string()
                )
            finally:
                server.quit()
            logger.info("The Record has been sent to ADMIN EMAIL successfully.")
        # SMTP adapters must not break application execution.
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Email Notifier failed to send the Record: %s", exc)
        finally:
            slot.release()
            if event is not None:
                event.set()

    try:
        worker = threading.Thread(
            target=send_email, name="dj-logging-email", daemon=True
        )
        worker.start()
    except Exception:
        slot.release()
        if event is not None:
            event.set()
        raise
    return True
