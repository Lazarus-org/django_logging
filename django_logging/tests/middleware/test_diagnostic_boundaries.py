"""Disabled paths, malformed diagnostics, and stream lifecycle cleanup."""

import logging
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import TooManyFieldsSent
from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory
from django.utils.timezone import now

from django_logging.contextvar import manager
from django_logging.middleware.monitor_log_size import MonitorLogSizeMiddleware
from django_logging.tests.middleware.test_request_hardening import middleware_with


def test_started_events_exact_exclusions_and_disabled_completion():
    middleware = middleware_with(
        {
            "LOG_REQUEST_STARTED": True,
            "LOG_REQUEST_FINISHED": False,
            "EXCLUDED_PATHS": ["/private"],
        }
    )
    assert middleware._values_excluded("/private")
    with patch("django_logging.middleware.request_middleware.logger") as log:
        assert middleware(RequestFactory().get("/public")).status_code == 200
    assert len(log.info.call_args_list) == 1
    assert "REQUEST STARTED" in log.info.call_args.args[0]


def test_query_missing_or_rejected_by_django_parser():
    middleware = middleware_with({"LOG_QUERY_PARAMS": True})
    request = RequestFactory().get("/")
    assert middleware._query_values(request) is None
    request.META["QUERY_STRING"] = "a=b"
    request.__dict__["GET"] = Mock()
    request.GET.lists.side_effect = TooManyFieldsSent("too many")
    assert middleware._query_values(request) == "<unparseable query string>"


@pytest.mark.parametrize(
    "method,content_type,body,length",
    [
        ("GET", "application/json", b"{}", "2"),
        ("POST", "text/plain", b"{}", "2"),
        ("POST", "application/json", b"{}", "0"),
        ("POST", "application/json", b"long body" * 10, "1"),
        ("POST", "application/json", b"{", "1"),
        ("POST", "application/json", b"1", "1"),
    ],
)
def test_request_body_failures_never_change_the_response(
    method, content_type, body, length
):
    middleware = middleware_with({"LOG_REQUEST_BODY": True, "MAX_BODY_BYTES": 8})
    request = RequestFactory().generic(
        method, "/", data=body, content_type=content_type
    )
    request.META["CONTENT_LENGTH"] = length
    assert middleware._request_body_values(request) is None
    assert middleware(request).status_code == 200


def test_error_diagnostics_are_bounded_and_fail_closed():
    middleware = middleware_with({"MAX_ERROR_BYTES": 8})
    stream = StreamingHttpResponse(iter([b"secret"]))
    assert middleware._safe_error_body(stream, "/") == "<streaming error response>"
    assert (
        middleware._safe_error_body(SimpleNamespace(), "/")
        == "<error details unavailable>"
    )
    assert (
        middleware._safe_error_body(SimpleNamespace(_container=["not bytes"]), "/")
        == "<error details unavailable>"
    )
    assert (
        middleware._safe_error_body(HttpResponse(b"x" * 9), "/")
        == "<oversized error response>"
    )
    with patch(
        "django_logging.middleware.request_middleware.safe_error_response",
        side_effect=RuntimeError("unavailable"),
    ):
        assert (
            middleware._safe_error_body(HttpResponse(b"{}"), "/")
            == "<error details unavailable>"
        )
    stream.close()


def test_direct_sync_stream_closes_source_in_context_and_restores_outer_context():
    middleware = middleware_with({"LOG_STREAMING_EVENTS": True})
    seen = []

    def source():
        try:
            yield b"one"
            yield b"two"
        finally:
            seen.append(manager.get_contextvars()["request_id"])

    with manager.scoped_context(request_id="outer"):
        stream = middleware._sync_streaming_wrapper(source(), "inner")
        assert next(stream) == b"one"
        stream.close()
        assert seen == ["inner"]
        assert manager.get_contextvars()["request_id"] == "outer"


@pytest.mark.asyncio
async def test_async_stream_finished_and_early_close_events():
    middleware = middleware_with({"LOG_STREAMING_EVENTS": True})
    closed = []

    async def source():
        try:
            yield b"one"
            yield b"two"
        finally:
            closed.append(manager.get_contextvars()["request_id"])

    with manager.scoped_context(request_id="outer"):
        complete = middleware._async_streaming_wrapper(source(), "complete")
        assert [chunk async for chunk in complete] == [b"one", b"two"]
        early = middleware._async_streaming_wrapper(source(), "early")
        assert await early.__anext__() == b"one"
        await early.aclose()
        assert closed == ["complete", "early"]
        assert manager.get_contextvars()["request_id"] == "outer"


def test_sql_diagnostics_reject_oversized_output():
    middleware = middleware_with({"MAX_SQL_BYTES": 1})
    assert (
        middleware._log_sql_queries(0, [{"time": "0.1", "sql": "SELECT secret"}])
        == "<oversized SQL log>"
    )


def test_optional_audit_handles_recent_corrupt_and_unavailable_cache():
    middleware = MonitorLogSizeMiddleware(lambda request: HttpResponse("ok"))
    with (
        patch("django_logging.middleware.monitor_log_size.cache") as cache,
        patch.object(middleware, "run_log_size_check") as audit,
    ):
        cache.get.return_value = now()
        middleware._maybe_audit()
        audit.assert_not_called()
        cache.get.return_value = "corrupt timestamp"
        assert middleware.should_run_task() is True
        cache.get.side_effect = RuntimeError("cache unavailable")
        with patch("django_logging.middleware.monitor_log_size.logger") as log:
            middleware._maybe_audit()
            log.exception.assert_called_once()
