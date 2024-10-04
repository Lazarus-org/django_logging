import sys
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now

from django_logging.middleware.monitor_log_size import MonitorLogSizeMiddleware
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.middleware,
    pytest.mark.monitor_log_size_middleware,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestMonitorLogSizeMiddleware:
    """
    Test suite for the MonitorLogSizeMiddleware class.
    """

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """
        Clears cache before each test.
        """
        cache.clear()

    def test_should_run_task_no_cache(self) -> None:
        """
        Test that the task should run when there is no cache entry for 'last_run_logs_size_audit'.
        """
        assert MonitorLogSizeMiddleware.should_run_task() is True

    def test_should_run_task_with_recent_cache(self) -> None:
        """
        Test that the task should not run if the cache indicates the last run was within a week.
        """
        last_run_time = now() - timedelta(days=2)
        cache.set("last_run_logs_size_audit", last_run_time)

        assert MonitorLogSizeMiddleware.should_run_task() is False

    def test_should_run_task_with_old_cache(self) -> None:
        """
        Test that the task should run if the cache indicates the last run was more than a week ago.
        """
        last_run_time = now() - timedelta(weeks=2)
        cache.set("last_run_logs_size_audit", last_run_time)

        assert MonitorLogSizeMiddleware.should_run_task() is True

    @patch("django_logging.middleware.monitor_log_size.call_command")
    def test_sync_run_log_size_check(self, mock_call_command: Mock) -> None:
        """
        Test the synchronous execution of the log size check.
        """
        mock_get_response = Mock(return_value=HttpResponse())
        middleware = MonitorLogSizeMiddleware(mock_get_response)

        request = HttpRequest()

        # Simulate no recent audit, so the task should run
        cache.set("last_run_logs_size_audit", now() - timedelta(weeks=2))

        response = middleware.__sync_call__(request)

        mock_call_command.assert_called_once_with("logs_size_audit")
        assert cache.get("last_run_logs_size_audit") is not None
        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("django_logging.middleware.monitor_log_size.call_command")
    async def test_async_run_log_size_check(self, mock_call_command: Mock) -> None:
        """
        Test the asynchronous execution of the log size check.
        """

        async def mock_get_response(request: HttpRequest) -> HttpResponse:
            return HttpResponse()

        middleware = MonitorLogSizeMiddleware(mock_get_response)

        request = HttpRequest()

        # Simulate no recent audit, so the task should run
        cache.set("last_run_logs_size_audit", now() - timedelta(weeks=2))

        response = await middleware.__acall__(request)

        mock_call_command.assert_called_once_with("logs_size_audit")
        assert cache.get("last_run_logs_size_audit") is not None
        assert response.status_code == 200

    @patch(
        "django_logging.middleware.monitor_log_size.call_command", side_effect=Exception("Command failed")
    )
    def test_sync_run_log_size_check_failure(self, mock_call_command: Mock) -> None:
        """
        Test error handling in the synchronous log size check.
        """
        mock_get_response = Mock(return_value=HttpResponse())
        middleware = MonitorLogSizeMiddleware(mock_get_response)

        request = HttpRequest()

        with patch(
            "django_logging.middleware.monitor_log_size.logger.error"
        ) as mock_logger:
            middleware.__sync_call__(request)

            mock_call_command.assert_called_once_with("logs_size_audit")
            mock_logger.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "django_logging.middleware.monitor_log_size.call_command", side_effect=Exception("Command failed")
    )
    async def test_async_run_log_size_check_failure(self, mock_call_command: Mock) -> None:
        """
        Test error handling in the asynchronous log size check.
        """

        async def mock_get_response(request):
            return HttpResponse()

        middleware = MonitorLogSizeMiddleware(mock_get_response)

        request = HttpRequest()

        with patch(
                "django_logging.middleware.monitor_log_size.logger.error"
        ) as mock_logger:
            await middleware.__acall__(request)

            mock_call_command.assert_called_once_with("logs_size_audit")
            mock_logger.assert_called_once()

