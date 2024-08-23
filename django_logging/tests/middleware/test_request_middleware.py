import logging
from unittest.mock import Mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django_logging.middleware import RequestLogMiddleware


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def get_response():
    def _get_response(request):
        return HttpResponse("Test Response")

    return _get_response


@pytest.fixture
def middleware(get_response):
    return RequestLogMiddleware(get_response)


def test_authenticated_user_logging(middleware, request_factory, caplog):
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


def test_anonymous_user_logging(middleware, request_factory, caplog):
    request = request_factory.get("/test-path")
    request.user = AnonymousUser()

    with caplog.at_level(logging.INFO):
        middleware(request)

    assert "Request Info" in caplog.text
    assert "Anonymous" in caplog.text


def test_ip_address_extraction(middleware, request_factory):
    request = request_factory.get("/test-path", HTTP_X_FORWARDED_FOR="192.168.1.1")

    middleware(request)

    assert request.ip_address == "192.168.1.1"


def test_user_agent_extraction(middleware, request_factory):
    request = request_factory.get("/test-path", HTTP_USER_AGENT="Mozilla/5.0")

    middleware(request)

    assert request.browser_type == "Mozilla/5.0"
