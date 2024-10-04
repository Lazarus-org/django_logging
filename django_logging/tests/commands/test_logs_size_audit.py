import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_logs_size_audit,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestCheckLogSizeCommand:
    """
    Test suite for the `check_log_size` management command.
    """

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    def test_command_log_directory_size_under_limit(
        self, mock_os_walk: MagicMock, temp_log_directory: str
    ) -> None:
        """
        Test that the command correctly handles the case when the log directory size is under the limit.

        This test verifies that the command calculates the log directory size correctly and does not send
        an email when the size is below the limit.

        Args:
            mock_os_walk (MagicMock): Mock for `os.walk`.
            temp_log_directory (str): Temporary log directory fixture.
        """
        # Mock the os.walk to return an empty directory
        mock_os_walk.return_value = [(temp_log_directory, [], [])]

        # Execute the command and capture the output
        out = StringIO()
        with patch("django.conf.settings.DJANGO_LOGGING", {"LOG_DIR_SIZE_LIMIT": 100}):
            call_command("logs_size_audit", stdout=out)

        assert "Log directory size is under the limit" in out.getvalue()

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    @patch("django_logging.management.commands.logs_size_audit.send_email_async")
    def test_command_log_directory_size_exceeds_limit(
        self,
        mock_send_email: MagicMock,
        mock_os_walk: MagicMock,
        temp_log_directory: str,
    ) -> None:
        """
        Test that the command sends a warning email when the log directory size exceeds the limit.

        This test verifies that the command calculates the log directory size correctly and sends
        an email notification when the size exceeds the limit.

        Args:
        ----
            mock_send_email (MagicMock): Mock for the `send_warning_email` method.
            mock_os_walk (MagicMock): Mock for `os.walk`.
            temp_log_directory (str): Temporary log directory fixture.
        """
        # Mock the os.walk to simulate a large directory
        mock_os_walk.return_value = [
            (temp_log_directory, [], ["log1.txt", "log2.txt"]),
        ]
        # Mock the file sizes to exceed the limit
        with patch("os.path.getsize", side_effect=[60 * 1024 * 1024, 50 * 1024 * 1024]):
            out = StringIO()
            with patch("django.conf.settings.ADMIN_EMAIL", "admin@example.com"):
                with patch("django.conf.settings.DJANGO_LOGGING", {"LOG_DIR_SIZE_LIMIT": 100}):
                    call_command("logs_size_audit", stdout=out)

        # Verify that the warning email was sent
        mock_send_email.assert_called_once()
        assert "Warning email sent successfully" in out.getvalue()

    @patch("os.path.exists", return_value=False)
    def test_command_log_directory_not_found(self, temp_log_directory: str) -> None:
        """
        Test that the command handles the case where the log directory does not exist.

        This test verifies that the command logs an error message and exits gracefully
        when the log directory is missing.

        Args:
        ----
            temp_log_directory (str): Temporary log directory fixture.
        """
        out = StringIO()
        call_command("logs_size_audit", stdout=out)

        assert "Log directory not found" in out.getvalue()
