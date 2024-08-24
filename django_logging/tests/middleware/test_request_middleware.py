import logging
from typing import Callable
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django_logging.middleware import RequestLogMiddleware


@pytest.fixture
def request_factory() -> RequestFactory:
    """
    Fixture to create a RequestFactory instance for generating request objects.

    Returns:
    -------
    RequestFactory
        An instance of RequestFactory for creating mock requests.
    """
    return RequestFactory()


@pytest.fixture
def get_response() -> Callable:
    """
    Fixture to create a mock get_response function.

    Returns:
    -------
    function
        A function that returns an HttpResponse with a dummy response.
    """

    def _get_response(request: RequestFactory) -> HttpResponse:
        return HttpResponse("Test Response")

    return _get_response


@pytest.fixture
def middleware(get_response: Callable) -> RequestLogMiddleware:
    """
    Fixture to create an instance of RequestLogMiddleware.

    Args:
    ----
    get_response : function
        A function that returns an HttpResponse for a given request.

    Returns:
    -------
    RequestLogMiddleware
        An instance of RequestLogMiddleware with the provided get_response function.
    """
    return RequestLogMiddleware(get_response)


def test_authenticated_user_logging(
    middleware: RequestLogMiddleware,
    request_factory: RequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test logging of requests for authenticated users.

    This test verifies that when an authenticated user makes a request,
    the relevant request information, including the username, is logged.

    Args:
    ----
    middleware : RequestLogMiddleware
        The middleware instance used to process the request.
    request_factory : RequestFactory
        A factory for creating mock HTTP requests.
    caplog : pytest.LogCaptureFixture
        A fixture for capturing log messages.

    Asserts:
    -------
    - "Request Info" is present in the logs.
    - The requested path is logged.
    - The username of the authenticated user is logged.
    - The request object has `ip_address` and `browser_type` attributes.
    """
    request = request_factory.get("/test-path")

    UserModel = get_user_model()
    username_field = UserModel.USERNAME_FIELD

    request.user = Mock()
    request.user.is_authenticated = True
    setattr(request.user, username_field, "test_user")

    with caplog.at_level(logging.INFO):
        middleware(request)

    assert "Request Info" in caplog.text
    assert "test-path" in caplog.text
    assert "test_user" in caplog.text
    assert request.ip_address
    assert request.browser_type


def test_anonymous_user_logging(
    middleware: RequestLogMiddleware,
    request_factory: RequestFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test logging of requests for anonymous users.

    This test ensures that when an anonymous user makes a request,
    the relevant request information, including the identification as "Anonymous", is logged.

    Args:
    ----
    middleware : RequestLogMiddleware
        The middleware instance used to process the request.
    request_factory : RequestFactory
        A factory for creating mock HTTP requests.
    caplog : pytest.LogCaptureFixture
        A fixture for capturing log messages.

    Asserts:
    -------
    - "Request Info" is present in the logs.
    - The request is identified as coming from an "Anonymous" user.
    """
    request = request_factory.get("/test-path")
    request.user = AnonymousUser()

    with caplog.at_level(logging.INFO):
        middleware(request)

    assert "Request Info" in caplog.text
    assert "Anonymous" in caplog.text


def test_ip_address_extraction(
    middleware: RequestLogMiddleware, request_factory: RequestFactory
) -> None:
    """
    Test extraction of the client's IP address from the request.

    This test verifies that the middleware correctly extracts the IP address
    from the `HTTP_X_FORWARDED_FOR` header in the request.

    Args:
    ----
    middleware : RequestLogMiddleware
        The middleware instance used to process the request.
    request_factory : RequestFactory
        A factory for creating mock HTTP requests.

    Asserts:
    -------
    - The `ip_address` attribute of the request is correctly set to the value in the `HTTP_X_FORWARDED_FOR` header.
    """
    request = request_factory.get("/test-path", HTTP_X_FORWARDED_FOR="192.168.1.1")

    middleware(request)

    assert request.ip_address == "192.168.1.1"


def test_user_agent_extraction(
    middleware: RequestLogMiddleware, request_factory: RequestFactory
) -> None:
    """
    Test extraction of the client's user agent from the request.

    This test verifies that the middleware correctly extracts the user agent
    from the `HTTP_USER_AGENT` header in the request.

    Args:
    ----
    middleware : RequestLogMiddleware
        The middleware instance used to process the request.
    request_factory : RequestFactory
        A factory for creating mock HTTP requests.

    Asserts:
    -------
    - The `browser_type` attribute of the request is correctly set to the value in the `HTTP_USER_AGENT` header.
    """
    request = request_factory.get("/test-path", HTTP_USER_AGENT="Mozilla/5.0")

    middleware(request)

    assert request.browser_type == "Mozilla/5.0"
