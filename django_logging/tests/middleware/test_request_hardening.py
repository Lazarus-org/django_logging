"""Regression coverage for request logging isolation, privacy and bounded work."""

import asyncio
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, override_settings
from django.utils.functional import SimpleLazyObject

from django_logging.contextvar import manager
from django_logging.middleware.request_middleware import RequestLogMiddleware
from django_logging.settings.checks import check_request_logging_settings


@pytest.fixture(autouse=True)
def clean_context():
    manager.clear()
    yield
    manager.clear()


def middleware_with(config, view=None, *, log_sql=False):
    with override_settings(
        DJANGO_LOGGING={
            "AUTO_INITIALIZATION_ENABLE": False,
            "REQUEST_LOGGING": config,
            "LOG_SQL_QUERIES_ENABLE": log_sql,
        }
    ):
        return RequestLogMiddleware(view or (lambda request: HttpResponse("OK")))


def test_existing_context_is_restored_on_success_and_exception():
    request = RequestFactory().get("/", HTTP_X_REQUEST_ID="inner")

    def response(request):
        assert manager.get_contextvars()["request_id"] == "inner"
        assert manager.get_contextvars()["tenant"] == "outer"
        return HttpResponse("ok")

    middleware = middleware_with({}, response)
    with manager.scoped_context(request_id="outer", tenant="outer"):
        assert middleware(request).status_code == 200
        assert manager.get_contextvars() == {"request_id": "outer", "tenant": "outer"}

        def explode(request):
            assert manager.get_contextvars()["request_id"] == "inner"
            raise RuntimeError("boom")

        failing = middleware_with({}, explode)
        with pytest.raises(RuntimeError):
            failing(RequestFactory().get("/", HTTP_X_REQUEST_ID="inner"))
        assert manager.get_contextvars() == {"request_id": "outer", "tenant": "outer"}


@pytest.mark.asyncio
async def test_concurrent_async_requests_isolate_context():
    entered = asyncio.Event()
    release = asyncio.Event()
    seen = []

    async def response(request):
        seen.append((request.request_id, manager.get_contextvars()["request_id"]))
        if request.request_id == "one":
            entered.set()
            await release.wait()
        else:
            release.set()
        seen.append((request.request_id, manager.get_contextvars()["request_id"]))
        return HttpResponse("OK")

    middleware = middleware_with({}, response)
    with manager.scoped_context(tenant="outer"):
        await asyncio.gather(
            middleware(RequestFactory().get("/a", HTTP_X_REQUEST_ID="one")),
            middleware(RequestFactory().get("/b", HTTP_X_REQUEST_ID="two")),
        )
        assert manager.get_contextvars() == {"tenant": "outer"}
    assert sorted(seen) == sorted(
        [("one", "one"), ("one", "one"), ("two", "two"), ("two", "two")]
    )
    assert not hasattr(middleware, "context")
    assert not hasattr(middleware, "initial_queries")


@pytest.mark.asyncio
async def test_async_cancellation_restores_original_context():
    async def cancelled(_request):
        raise asyncio.CancelledError

    middleware = middleware_with({}, cancelled)
    with manager.scoped_context(request_id="before"):
        with pytest.raises(asyncio.CancelledError):
            await middleware(RequestFactory().get("/"))
        assert manager.get_contextvars()["request_id"] == "before"


def test_lazy_user_is_not_resolved_for_logging():
    def explode():
        raise AssertionError("logging forced session lookup")

    request = RequestFactory().get("/")
    request.user = SimpleLazyObject(explode)
    middleware = middleware_with({})
    assert middleware(request).status_code == 200
    assert middleware.get_user(request) == "Anonymous"


def test_request_id_rejected_if_invalid_or_oversized():
    middleware = middleware_with({"MAX_REQUEST_ID_LENGTH": 40})
    for bad in ["hi\nspoof", "x" * 81, "á", "", "x y"]:
        request = RequestFactory().get("/", HTTP_X_REQUEST_ID=bad)
        middleware(request)
        assert request.request_id != bad
        assert len(request.request_id) == 36
    good = RequestFactory().get("/", HTTP_X_REQUEST_ID="a-b_01.xyz")
    middleware(good)
    assert good.request_id == "a-b_01.xyz"


def test_untrusted_proxy_is_ignored():
    middleware = middleware_with({"TRUSTED_PROXY_CIDRS": ["10.0.0.0/24"]})
    request = RequestFactory().get(
        "/", HTTP_X_REAL_IP="198.51.100.3", HTTP_X_FORWARDED_FOR="203.0.113.5"
    )
    request.META["REMOTE_ADDR"] = "192.0.2.2"
    assert middleware.get_ip_address(request) == "192.0.2.2"
    trusted = RequestFactory().get("/", HTTP_X_REAL_IP="198.51.100.3")
    trusted.META["REMOTE_ADDR"] = "10.0.0.3"
    assert middleware.get_ip_address(trusted) == "198.51.100.3"
    wrapped = type("DRFRequest", (), {"_request": trusted})()
    assert middleware.get_ip_address(wrapped) == "198.51.100.3"


def test_redaction_and_excluded_prefix_across_diagnostics():
    config = {
        "LOG_QUERY_PARAMS": True,
        "LOG_REQUEST_BODY": True,
        "LOG_ERROR_RESPONSE": True,
        "EXCLUDED_PATH_PREFIXES": ["/auth"],
        "EXCLUDED_FIELDS": ["custom_field"],
    }
    middleware = middleware_with(
        config,
        lambda _: HttpResponse(
            '{"password":"secret","result":"failed"}',
            status=400,
            content_type="application/json",
        ),
    )
    body = b'{"password":"private","items":[{"api_key":"abc"}],"safe":"ok"}'
    request = RequestFactory().post(
        "/plain?password=secret&search=hello&custom_field=my-secret",
        data=body,
        content_type="application/json",
    )
    with patch("django_logging.middleware.request_middleware.logger") as log:
        middleware(request)
        rendered = " ".join(
            str(call.args[0] % call.args[1:]) for call in log.info.call_args_list
        )
        assert '"search":"hello"' in rendered
        assert "my-secret" not in rendered
        assert "private" not in rendered
        assert '"safe":"ok"' in rendered
        assert '"password":"[REDACTED]"' in rendered
    private = RequestFactory().post(
        "/auth/login?password=secret",
        data=body,
        content_type="application/json",
    )
    with patch("django_logging.middleware.request_middleware.logger") as log:
        middleware(private)
        rendered = " ".join(
            str(call.args[0] % call.args[1:]) for call in log.info.call_args_list
        )
        assert "secret" not in rendered
        assert "private" not in rendered
        assert "query_params=None" in rendered
        assert "request_payload=None" in rendered
        assert "response=None" in rendered


def test_bounded_diagnostics_and_disabled_body_reads():
    request = RequestFactory().post(
        "/", data=b'{"key":"value"}', content_type="application/json"
    )
    with patch.object(
        type(request),
        "body",
        property(lambda _: (_ for _ in ()).throw(AssertionError("body accessed"))),
    ):
        assert middleware_with({})(request).status_code == 200
    middleware = middleware_with({"LOG_QUERY_PARAMS": True, "MAX_QUERY_BYTES": 8})
    with patch("django_logging.middleware.request_middleware.logger") as log:
        middleware(RequestFactory().get("/?value=123456789"))
        rendered = " ".join(
            str(call.args[0] % call.args[1:]) for call in log.info.call_args_list
        )
        assert "<oversized query string>" in rendered


def test_stream_context_restored_after_consumption():
    def view(_request):
        def source():
            assert manager.get_contextvars()["request_id"] == "stream-id"
            yield b"a"
            assert manager.get_contextvars()["request_id"] == "stream-id"
            yield b"b"

        return StreamingHttpResponse(source())

    middleware = middleware_with({}, view)
    request = RequestFactory().get("/", HTTP_X_REQUEST_ID="stream-id")
    response = middleware(request)
    assert "request_id" not in manager.get_contextvars()
    assert list(response.streaming_content) == [b"a", b"b"]
    assert "request_id" not in manager.get_contextvars()


@pytest.mark.asyncio
async def test_async_stream_context_restored():
    async def view(_request):
        async def source():
            assert manager.get_contextvars()["request_id"] == "stream-id"
            yield b"a"

        return StreamingHttpResponse(source())

    middleware = middleware_with({}, view)
    response = await middleware(
        RequestFactory().get("/", HTTP_X_REQUEST_ID="stream-id")
    )
    assert [chunk async for chunk in response.streaming_content] == [b"a"]
    assert "request_id" not in manager.get_contextvars()


@pytest.mark.parametrize(
    "config",
    [
        {"NOT_A_REAL_SETTING": True},
        {"MAX_BODY_BYTES": -1},
        {"MAX_QUERY_BYTES": True},
        {"MAX_REQUEST_ID_LENGTH": "80"},
        {"LOG_QUERY_PARAMS": "yes"},
        {"TRUSTED_PROXY_CIDRS": ["not-a-network"]},
        {"EXCLUDED_FIELDS_BY_PATH": {"path": ["token"]}},
        [],
    ],
)
def test_invalid_settings_fail_activation_and_django_checks(config):
    with override_settings(DJANGO_LOGGING={"REQUEST_LOGGING": config}):
        assert check_request_logging_settings(None)
        with pytest.raises(ImproperlyConfigured):
            RequestLogMiddleware(lambda request: HttpResponse("OK"))


@pytest.mark.asyncio
async def test_stream_can_be_closed_from_another_task_without_context_token_leak():
    async def view(_request):
        async def source():
            yield b"first"
            yield b"second"

        return StreamingHttpResponse(source())

    middleware = middleware_with({}, view)
    response = await middleware(RequestFactory().get("/", HTTP_X_REQUEST_ID="abc"))
    stream = response.streaming_content
    assert await stream.__anext__() == b"first"
    assert "request_id" not in manager.get_contextvars()
    # Closing the stream from a different task must not try to reset a token
    # belonging to the task that consumed its first chunk.
    await asyncio.create_task(stream.aclose())
    assert "request_id" not in manager.get_contextvars()


def test_query_value_serialization_limit_applies_after_parsing():
    middleware = middleware_with({"LOG_QUERY_PARAMS": True, "MAX_QUERY_BYTES": 12})
    request = RequestFactory().get("/?q=%0A%0A%0A")
    with patch("django_logging.middleware.request_middleware.logger") as log:
        middleware(request)
        rendered = " ".join(
            str(call.args[0] % call.args[1:]) for call in log.info.call_args_list
        )
    assert "<oversized query string>" in rendered


def test_request_context_not_left_on_early_sync_stream_close():
    closed = []

    def response(_request):
        def source():
            try:
                yield b"chunk"
                yield b"last"
            finally:
                closed.append(manager.get_contextvars().get("request_id"))

        return StreamingHttpResponse(source())

    middleware = middleware_with({}, response)
    result = middleware(RequestFactory().get("/", HTTP_X_REQUEST_ID="early"))
    iterator = result.streaming_content
    assert next(iterator) == b"chunk"
    assert "request_id" not in manager.get_contextvars()
    result.close()
    assert closed == ["early"]
    assert "request_id" not in manager.get_contextvars()


def test_safe_path_fast_path_preserves_printable_paths_and_sanitizes_controls():
    assert RequestLogMiddleware._safe_path("/api/v1/orders/") == "/api/v1/orders/"
    assert RequestLogMiddleware._safe_path("/api/\x00orders/\n") == "/api/?orders/?"
    assert len(RequestLogMiddleware._safe_path("/" + "a" * 1000)) == 256


def test_stream_lifecycle_events_are_disabled_by_default():
    middleware = middleware_with({})

    def view(_request):
        return StreamingHttpResponse(iter([b"one", b"two"]))

    middleware.get_response = view
    request = RequestFactory().get("/")
    with patch("django_logging.middleware.request_middleware.logger") as log:
        response = middleware(request)
        assert list(response.streaming_content) == [b"one", b"two"]
    assert not any(
        "Streaming started" in str(call.args[0])
        or "Streaming finished" in str(call.args[0])
        for call in log.info.call_args_list
    )


def test_stream_lifecycle_events_can_be_enabled_explicitly():
    middleware = middleware_with({"LOG_STREAMING_EVENTS": True})

    def view(_request):
        return StreamingHttpResponse(iter([b"one"]))

    middleware.get_response = view
    with patch("django_logging.middleware.request_middleware.logger") as log:
        response = middleware(RequestFactory().get("/"))
        assert list(response.streaming_content) == [b"one"]
    messages = [call.args[0] for call in log.info.call_args_list]
    assert any("Streaming started" in message for message in messages)
    assert any("Streaming finished" in message for message in messages)
