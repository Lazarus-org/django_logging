"""Production hardening regression checks for bounded notifier and rotator."""

import gzip
import logging
import threading
from unittest.mock import patch

from django_logging.handlers.rotating_file_handler import _gzip_rotator
from django_logging.utils.log_email_notifier import notifier


def test_failed_compression_keeps_original_file(tmp_path):
    source = tmp_path / "error.log"
    source.write_bytes(b"retained on failure")
    dest = tmp_path / "error.log.1.gz"
    with patch(
        "django_logging.handlers.rotating_file_handler.shutil.copyfileobj",
        side_effect=OSError("disk full"),
    ):
        try:
            _gzip_rotator(str(source), str(dest))
        except OSError:
            pass
        else:
            raise AssertionError("Expected compression failure")
    assert source.read_bytes() == b"retained on failure"
    assert not dest.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["error.log"]


def test_compression_produces_complete_gzip(tmp_path):
    source = tmp_path / "error.log"
    source.write_bytes(b"some data")
    dest = tmp_path / "error.log.1.gz"
    _gzip_rotator(str(source), str(dest))
    assert not source.exists()
    with gzip.open(dest, "rb") as gz:
        assert gz.read() == b"some data"


def test_email_delivery_is_bounded_and_nonblocking(settings):
    settings.DJANGO_LOGGING = {
        "LOG_EMAIL_NOTIFIER": {"MAX_CONCURRENT": 1, "SMTP_TIMEOUT": 2}
    }
    started = threading.Event()
    release = threading.Event()
    completed = threading.Event()

    def blocked_smtp(*args, **kwargs):
        started.set()
        assert release.wait(3)
        raise OSError("test expected")

    try:
        with patch.object(notifier, "SMTP", side_effect=blocked_smtp):
            assert notifier.send_email_async(
                "one", "body", ["admin@example.com"], completed
            )
            assert started.wait(2)
            dropped_event = threading.Event()
            assert (
                notifier.send_email_async(
                    "two", "body", ["admin@example.com"], dropped_event
                )
                is False
            )
            assert dropped_event.is_set()
    finally:
        release.set()
        assert completed.wait(3)


def test_bad_email_limits_fail_early(settings):
    settings.DJANGO_LOGGING = {"LOG_EMAIL_NOTIFIER": {"MAX_CONCURRENT": 0}}
    with patch.object(notifier, "SMTP") as smtp:
        try:
            notifier.send_email_async("x", "y", ["a@example.com"])
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid limits must raise")
        smtp.assert_not_called()
