"""Fail-closed diagnostics, notifier resource release, and archive safety."""

import os
import runpy
import threading
from unittest.mock import Mock, patch

import pytest

from django_logging.management.commands.archive_logs import Command
from django_logging.utils.log_email_notifier import notifier
from django_logging.utils.redaction import (
    diagnostic_json,
    redact_values,
    safe_error_response,
)
from django_logging.utils.request import _parse_ip


def test_redaction_depth_and_unserializable_diagnostic():
    assert redact_values({"child": {"secret": "hidden"}}, max_depth=1) == {
        "child": "[OMITTED]"
    }
    assert (
        diagnostic_json(object(), max_bytes=100, oversized="large")
        == "<unserializable diagnostic>"
    )


@pytest.mark.parametrize(
    "body,content_type,limit,expected",
    [
        (b"private", "text/plain", 100, "<non-json error response>"),
        (b"{}", "application/json", 1, "<oversized error response>"),
        (b"{", "application/json", 100, "<unparseable error response>"),
        (b"[]", "application/json", 100, "<unstructured error response>"),
    ],
)
def test_error_response_rejections(body, content_type, limit, expected):
    assert (
        safe_error_response(body, content_type, max_bytes=limit, max_depth=2)
        == expected
    )


def test_invalid_ip_is_not_trusted():
    assert _parse_ip("not an address") is None


def test_notifier_settings_fallback_and_timeout_validation(settings):
    settings.DJANGO_LOGGING = {"LOG_EMAIL_NOTIFIER": []}
    assert notifier._options() == (4, 10)
    settings.DJANGO_LOGGING = {"LOG_EMAIL_NOTIFIER": {"SMTP_TIMEOUT": 0}}
    with pytest.raises(ValueError, match="SMTP_TIMEOUT"):
        notifier._options()


def test_failed_worker_start_releases_slot_and_sets_completion(settings):
    settings.DJANGO_LOGGING = {"LOG_EMAIL_NOTIFIER": {"MAX_CONCURRENT": 1}}
    notifier._after_fork()
    done = threading.Event()
    with patch.object(
        notifier.threading.Thread, "start", side_effect=RuntimeError("cannot start")
    ):
        with pytest.raises(RuntimeError, match="cannot start"):
            notifier.send_email_async("subject", "body", ["a@example.com"], done)
    assert done.is_set()
    slot = notifier._semaphore(1)
    assert slot.acquire(blocking=False)
    slot.release()


def test_fork_registration_discards_inherited_locks(monkeypatch):
    register = Mock()
    monkeypatch.setattr(os, "register_at_fork", register, raising=False)
    module = runpy.run_path(notifier.__file__)
    register.assert_called_once_with(after_in_child=module["_after_fork"])
    callback = register.call_args.kwargs["after_in_child"]
    old_lock = callback.__globals__["_limiter_lock"]
    callback()
    assert callback.__globals__["_limiter_lock"] is not old_lock
    assert callback.__globals__["_limiter"] is None


def test_archive_rejects_paths_outside_log_directory(tmp_path):
    root = tmp_path / "logs"
    root.mkdir()
    outside = tmp_path / "outside.log.1"
    outside.write_text("keep me")
    with patch(
        "django_logging.management.commands.archive_logs.settings_manager.log_dir",
        str(root),
    ):
        with pytest.raises(ValueError, match="escapes"):
            Command()._move_files([str(outside)], str(root / "archive"), False)
    assert outside.read_text() == "keep me"


def test_archive_collision_does_not_overwrite_existing_file(tmp_path):
    source = tmp_path / "info.log.1"
    source.write_text("keep me")
    with patch(
        "django_logging.management.commands.archive_logs.settings_manager.log_dir",
        str(tmp_path),
    ):
        with pytest.raises(FileExistsError):
            Command()._move_files(
                [str(source), str(source)], str(tmp_path / "archive"), False
            )
    assert (tmp_path / "archive" / source.name).read_text() == "keep me"
