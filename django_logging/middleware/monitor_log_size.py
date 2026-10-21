"""Legacy log-size audit middleware.

The inexpensive default is a pass-through: schedule ``logs_size_audit``
with cron/systemd/Beat instead. Running filesystem audits on HTTP
requests requires explicit LOG_SIZE_AUDIT_IN_REQUEST=True and is
discouraged in production.

"""

import logging
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpRequest, HttpResponseBase
from django.utils.timezone import now

from django_logging.middleware.base import BaseMiddleware

logger = logging.getLogger(__name__)
LAST_RUN_KEY = "last_run_logs_size_audit"
CLAIM_KEY = "dj_logging:log_size_audit:claim"
WEEK_SECONDS = 7 * 24 * 60 * 60


class MonitorLogSizeMiddleware(BaseMiddleware):
    """Optional legacy audit-on-request behavior, disabled by default."""

    @staticmethod
    def enabled() -> bool:
        config = getattr(settings, "DJANGO_LOGGING", {})
        return (
            isinstance(config, dict)
            and config.get("LOG_SIZE_AUDIT_IN_REQUEST", False) is True
        )

    def __sync_call__(self, request: HttpRequest) -> HttpResponseBase:
        if self.enabled():
            self._maybe_audit()
        return self.get_response(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        if self.enabled():
            await sync_to_async(self._maybe_audit, thread_sensitive=True)()
        return await self.get_response(request)

    @staticmethod
    def should_run_task() -> bool:
        last_run = cache.get(LAST_RUN_KEY)
        if last_run is None:
            return True
        try:
            return now() - last_run > timedelta(weeks=1)
        except (TypeError, ValueError):
            return True

    def _maybe_audit(self) -> None:
        try:
            if not self.should_run_task():
                return
            # cache.add suppresses overlap for a shared cache backend. On
            # failure the claim expires after five minutes (retry backoff).
            if not cache.add(CLAIM_KEY, "running", timeout=300):
                return
            if self.run_log_size_check():
                cache.set(LAST_RUN_KEY, now(), timeout=None)
                cache.delete(CLAIM_KEY)
        except Exception:  # pylint: disable=broad-exception-caught
            # The optional audit must never turn a healthy HTTP response into
            # a failure, even if the cache itself is unavailable.
            logger.exception("Log size audit scheduling failed")

    def run_log_size_check(self) -> bool:
        """Run the command, returning success without changing request
        outcome."""
        try:
            call_command("logs_size_audit")
            return True
        # Third-party commands must not change the HTTP response on failure.
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Error running 'logs_size_audit' command")
            return False
