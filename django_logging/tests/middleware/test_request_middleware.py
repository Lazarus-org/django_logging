import asyncio
import io
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.handlers.asgi import ASGIRequest
from django.db import connection
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.test import RequestFactory

from django_logging.middleware import RequestLogMiddleware
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.middleware,
    pytest.mark.request_middleware,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestRequestMiddleware:

    @pytest.mark.django_db
    def test_sync_sql_logging(
        self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware
    ) -> None:
        """
        Test that SQL query logging works for synchronous requests.

        Asserts:
        -------
            - SQL queries are logged when `self.log_sql` is True.
        """
        request = request_factory.get("/")
        request.user = AnonymousUser()

        # Simulate an SQL query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        response = request_middleware(request)

        assert response.status_code == 200
        # If possible, capture the logger output to assert SQL logging

    @pytest.mark.asyncio
    async def test_async_request(self, request_factory: RequestFactory) -> None:
        """
        Test handling of an asynchronous request with RequestLogMiddleware.

        Asserts:
        -------
            - The middleware processes the asynchronous request successfully and returns a response.
        """
        request = request_factory.get("/")
        request.user = AnonymousUser()

        async def async_get_response(request: HttpRequest) -> HttpResponse:
            return HttpResponse("OK")

        middleware = RequestLogMiddleware(async_get_response)
        middleware.log_sql = True

        # Convert HttpRequest to ASGIRequest for async behavior
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        }

        body_file = io.BytesIO(b"")
        # Create an ASGIRequest object
        asgi_request = ASGIRequest(scope, body_file)
        response = await middleware(asgi_request)
        assert response.status_code == 200
        assert "OK" in response.content.decode()

        # Test exception block
        async def async_get_response_with_error(request: HttpRequest) -> HttpResponse:
            raise asyncio.CancelledError()

        middleware = RequestLogMiddleware(async_get_response_with_error)

        with pytest.raises(asyncio.CancelledError):
            await middleware(asgi_request)

    @pytest.mark.django_db
    def test_request_id_header(
        self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware
    ) -> None:
        """
        Test that RequestLogMiddleware retrieves the request ID from the headers.

        Asserts:
        -------
            - The request ID is correctly retrieved from the request headers.
        """
        request = request_factory.get("/")
        request.headers = {"x-request-id": "12345"}
        request.user = AnonymousUser()

        response = request_middleware(request)

        assert response.status_code == 200
        assert request_middleware.context["request_id"] == "12345"

    @pytest.mark.asyncio
    async def test_async_streaming_response(
        self, request_factory: RequestFactory
    ) -> None:
        """
        Test handling of asynchronous streaming responses with RequestLogMiddleware.

        Asserts:
        -------
            - The middleware handles asynchronous streaming responses correctly.
        """
        request = request_factory.get("/")
        request.user = AnonymousUser()

        async def streaming_response(request: HttpRequest) -> StreamingHttpResponse:
            async def generator() -> AsyncGenerator:
                for chunk in [b"chunk1", b"chunk2"]:
                    yield chunk

            _response = StreamingHttpResponse(generator())
            return _response

        middleware = RequestLogMiddleware(streaming_response)

        response = await middleware(request)

        assert response.status_code == 200
        assert response.streaming
        # Assert the streaming content
        streaming_content = [chunk async for chunk in response.streaming_content]
        assert streaming_content == [b"chunk1", b"chunk2"]

        # Test exception handling in sync_streaming_wrapper

    def test_sync_streaming_wrapper(
        self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware
    ) -> None:
        """
        Test that the sync_streaming_wrapper handles StreamingHttpResponse and exceptions correctly.
        """

        def streaming_view(request: HttpRequest) -> StreamingHttpResponse:
            def generator() -> Generator:
                yield b"chunk1"
                yield b"chunk2"

            return StreamingHttpResponse(generator())

        request = request_factory.get("/")
        request.user = AnonymousUser()

        middleware = RequestLogMiddleware(streaming_view)

        with patch(
            "django_logging.middleware.request_middleware.logger"
        ) as mock_logger:
            response = middleware(request)
            assert response.status_code == 200
            assert response.streaming

    def test_sync_streaming_wrapper_raises_exception(self, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that sync_streaming_wrapper handles an exception during streaming.

        Steps:
            - Mock the streaming content to raise an exception.
            - Assert that the exception is logged and re-raised.
        """

        request_id = "test-request-id"

        # Mock the streaming content to raise an exception when iterated
        streaming_content = MagicMock()
        streaming_content.__iter__.side_effect = Exception("Test Exception")

        # Patch the logger to check for log messages
        with patch(
            "django_logging.middleware.request_middleware.logger"
        ) as mock_logger:
            with pytest.raises(Exception, match="Test Exception"):
                list(
                    request_middleware._sync_streaming_wrapper(
                        streaming_content, request_id
                    )
                )

            # Check that logger.exception was called with the correct message
            mock_logger.exception.assert_called_once_with(
                "Streaming failed: request_id=%s", request_id
            )

    @pytest.mark.asyncio
    async def test_async_streaming_wrapper_cancelled_error(self, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that async_streaming_wrapper handles asyncio.CancelledError properly.

        Steps:
            - Mock the streaming content to raise asyncio.CancelledError.
            - Assert that the cancellation is logged and re-raised.
        """

        request_id = "test-request-id"

        # Mock the streaming content to raise asyncio.CancelledError
        streaming_content = AsyncMock()
        streaming_content.__aiter__.side_effect = asyncio.CancelledError

        # Patch the logger to check for log messages
        with patch(
            "django_logging.middleware.request_middleware.logger"
        ) as mock_logger:
            with pytest.raises(asyncio.CancelledError):
                async for _ in request_middleware._async_streaming_wrapper(
                    streaming_content, request_id
                ):
                    pass

            # Check that logger.warning was called with the correct message
            mock_logger.warning.assert_called_once_with(
                "Streaming was cancelled: request_id=%s", request_id
            )

    @pytest.mark.asyncio
    async def test_async_streaming_wrapper_generic_exception(self, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that async_streaming_wrapper handles a generic Exception properly.

        Steps:
            - Mock the streaming content to raise a generic Exception.
            - Assert that the exception is logged and re-raised.
        """

        request_id = "test-request-id"

        # Mock the streaming content to raise a generic Exception
        streaming_content = AsyncMock()
        streaming_content.__aiter__.side_effect = Exception("Test Exception")

        # Patch the logger to check for log messages
        with patch(
            "django_logging.middleware.request_middleware.logger"
        ) as mock_logger:
            with pytest.raises(Exception, match="Test Exception"):
                async for _ in request_middleware._async_streaming_wrapper(
                    streaming_content, request_id
                ):
                    pass

            # Check that logger.exception was called with the correct message
            mock_logger.exception.assert_called_once_with(
                "Streaming failed: request_id=%s", request_id
            )

    def test_sync_streaming_response_wrapper(self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that the synchronous streaming wrapper works correctly.
        """

        def streaming_view(request: HttpRequest) -> StreamingHttpResponse:
            return StreamingHttpResponse(iter([b"chunk1", b"chunk2"]))

        request = request_factory.get("/")
        request.user = AnonymousUser()

        # Wrap the streaming content in the middleware
        middleware = RequestLogMiddleware(streaming_view)
        response = middleware(request)

        assert response.status_code == 200
        assert response.streaming
        # Assert the streaming content
        streaming_content = list(response.streaming_content)
        assert streaming_content == [b"chunk1", b"chunk2"]

    @pytest.mark.django_db
    def test_get_user_authenticated(self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that the middleware retrieves the correct username for authenticated users.
        """
        user = User.objects.create(username="testuser")

        request = request_factory.get("/")
        request.user = user

        response = request_middleware(request)

        assert response.status_code == 200
        assert request_middleware.get_user(request) == f"[testuser (ID:{user.pk})]"

    def test_get_user_anonymous(self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that the middleware retrieves 'Anonymous' for unauthenticated users.
        """
        request = request_factory.get("/")
        request.user = AnonymousUser()

        response = request_middleware(request)

        assert response.status_code == 200
        assert request_middleware.get_user(request) == "Anonymous"

    def test_get_ip_address(self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that the middleware correctly retrieves the client's IP address.
        """
        request = request_factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.user = AnonymousUser()

        response = request_middleware(request)

        assert response.status_code == 200
        assert request_middleware.get_ip_address(request) == "192.168.1.1"

        request.META["REMOTE_ADDR"] = None

        request.META["HTTP_X_FORWARDED_FOR"] = "192.168.1.1,"
        assert request_middleware.get_ip_address(request) == "192.168.1.1"

        request.ip_address = "192.168.1.1"
        assert request_middleware.get_ip_address(request) == "192.168.1.1"

    def test_get_request_id(self, request_factory: RequestFactory, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that the middleware correctly retrieves the request ID from headers.
        """
        request = request_factory.get("/")
        request.headers = {"x-request-id": "12345"}
        request.user = AnonymousUser()

        response = request_middleware(request)

        assert response.status_code == 200
        assert request_middleware.get_request_id(request) == "12345"

        request.headers = {}
        request.META["HTTP_X_REQUEST_ID"] = "12345"
        request_middleware(request)
        assert request_middleware.get_request_id(request) == "12345"

    def test_log_sql_queries_with_queries(self, request_middleware: RequestLogMiddleware) -> None:
        """
        Test that _log_sql_queries correctly logs and formats SQL queries.
        """

        # Simulated SQL queries (new_queries in the method)
        mock_queries = [
            {"time": "0.002", "sql": "SELECT * FROM my_table WHERE id = 1"},
            {"time": "0.004", "sql": "UPDATE my_table SET value = 'test' WHERE id = 1"},
        ]

        log_output = request_middleware._log_sql_queries(0, mock_queries)

        # Assert that the log output executed
        assert log_output
