import sys
from typing import Callable
from unittest.mock import Mock

import pytest
from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponseBase

from django_logging.middleware.base import BaseMiddleware
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.middleware,
    pytest.mark.base_middleware,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestBaseMiddleware:
    """
    Test suite for the BaseMiddleware class.
    """

    def test_sync_mode(self) -> None:
        """
        Test that the middleware correctly identifies and handles synchronous requests.
        This test verifies that when the `get_response` function is synchronous,
        the middleware calls the `__sync_call__` method.
        """
        # Mock synchronous get_response
        mock_get_response = Mock(spec=Callable[[HttpRequest], HttpResponseBase])

        # Create an instance of the middleware
        middleware = BaseMiddleware(mock_get_response)

        # Ensure that it is in synchronous mode
        assert not iscoroutinefunction(middleware.get_response)
        assert not middleware.async_mode

        # Test that calling the middleware raises NotImplementedError (since __sync_call__ is not implemented)
        with pytest.raises(
            NotImplementedError, match="__sync_call__ must be implemented by subclass"
        ):
            request = HttpRequest()
            middleware(request)

    @pytest.mark.asyncio
    async def test_async_mode(self) -> None:
        """
        Test that the middleware correctly identifies and handles asynchronous requests.
        This test verifies that when the `get_response` function is asynchronous,
        the middleware calls the `__acall__` method.
        """

        # Mock asynchronous get_response
        async def mock_get_response(request: HttpRequest) -> HttpResponseBase:
            return Mock(spec=HttpResponseBase)

        # Create an instance of the middleware
        middleware = BaseMiddleware(mock_get_response)

        # Ensure that it is in asynchronous mode
        assert iscoroutinefunction(middleware.get_response)
        assert middleware.async_mode

        # Test that calling the middleware raises NotImplementedError (since __acall__ is not implemented)
        with pytest.raises(
            NotImplementedError, match="__acall__ must be implemented by subclass"
        ):
            request = HttpRequest()
            await middleware(request)
