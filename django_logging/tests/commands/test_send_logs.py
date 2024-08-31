import os
import shutil
import sys
import tempfile
from unittest.mock import ANY, Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_send_logs,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class SendLogsCommandTests(TestCase):
    """
    Test suite for the `send_logs` management command in the django_logging package.
    """

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    @patch("django_logging.management.commands.send_logs.shutil.make_archive")
    @patch("django_logging.management.commands.send_logs.EmailMessage")
    def test_handle_success(
        self,
        mock_email_message: Mock,
        mock_make_archive: Mock,
        mock_validate_email_settings: Mock,
    ) -> None:
        """
        Test that the `send_logs` command successfully creates an archive of the logs
        and sends an email when executed with valid settings.

        Args:
        ----
            mock_email_message: Mock for the `EmailMessage` class used to send the email.
            mock_make_archive: Mock for the `shutil.make_archive` function that creates the log archive.
            mock_validate_email_settings: Mock for the `validate_email_settings` method in the command.

        Asserts:
        -------
            - The `validate_email_settings` method is called exactly once.
            - The `shutil.make_archive` function is called with the correct arguments.
            - The `EmailMessage` is instantiated and sent.
        """
        temp_log_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        mock_make_archive.return_value = temp_file.name

        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            call_command("send_logs", "test@example.com")

        mock_validate_email_settings.assert_called_once()
        mock_make_archive.assert_called_once_with(ANY, "zip", temp_log_dir)
        mock_email_message.assert_called_once()

        shutil.rmtree(temp_log_dir)
        (
            os.remove(temp_file.name + ".zip")
            if os.path.exists(temp_file.name + ".zip")
            else None
        )

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    @patch("django_logging.management.commands.send_logs.EmailMessage.send")
    def test_handle_email_send_failure(
        self, mock_email_send: Mock, mock_validate_email_settings: Mock
    ) -> None:
        """
        Test that the `send_logs` command handles email sending failures correctly
        and logs an appropriate error message.

        Args:
        ----
            mock_email_send: Mock for the `EmailMessage.send` method, simulating a failure.
            mock_validate_email_settings: Mock for the `validate_email_settings` method in the command.

        Asserts:
        -------
            - An error message is logged when the email sending fails.
        """
        temp_log_dir = tempfile.mkdtemp()
        mock_email_send.side_effect = Exception("Email send failed")

        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            with self.assertLogs(
                "django_logging.management.commands.send_logs", level="ERROR"
            ) as cm:
                call_command("send_logs", "test@example.com")

        self.assertIn(
            "ERROR:django_logging.management.commands.send_logs:Failed to send logs: Email send failed",
            cm.output,
        )

        shutil.rmtree(temp_log_dir)

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    def test_handle_missing_log_dir(self, mock_validate_email_settings: Mock) -> None:
        """
        Test that the `send_logs` command logs an error when the specified log directory does not exist
        and skips the email validation step.

        Args:
        ----
            mock_validate_email_settings: Mock for the `validate_email_settings` method in the command.

        Asserts:
        -------
            - An error message is logged if the log directory does not exist.
            - The `validate_email_settings` method is not called.
        """
        non_existent_dir = "/non/existent/directory"
        with self.settings(DJANGO_LOGGING={"LOG_DIR": non_existent_dir}):
            with self.assertLogs(
                "django_logging.management.commands.send_logs", level="ERROR"
            ) as cm:
                call_command("send_logs", "test@example.com")

        self.assertIn(
            f"ERROR:django_logging.management.commands.send_logs:Log directory '{non_existent_dir}' does not exist.",
            cm.output,
        )
        mock_validate_email_settings.assert_not_called()

    @patch(
        "django_logging.management.commands.send_logs.check_email_settings",
        return_value=None,
    )
    def test_validate_email_settings_success(
        self, mock_check_email_settings: Mock
    ) -> None:
        """
        Test that the `validate_email_settings` method successfully validates the email settings
        without raising any exceptions.

        Args:
        ----
            mock_check_email_settings: Mock for the `check_email_settings` function, simulating a successful check.

        Asserts:
        -------
            - The `check_email_settings` function is called exactly once.
        """
        call_command("send_logs", "test@example.com")
        mock_check_email_settings.assert_called_once()

    @patch(
        "django_logging.management.commands.send_logs.check_email_settings",
        return_value="Missing config",
    )
    def test_validate_email_settings_failure(
        self, mock_check_email_settings: Mock
    ) -> None:
        """
        Test that the `validate_email_settings` method raises an `ImproperlyConfigured` exception
        when the email settings are invalid.

        Args:
        ----
            mock_check_email_settings: Mock for the `check_email_settings` function, simulating a failure.

        Asserts:
        -------
            - An `ImproperlyConfigured` exception is raised when email settings are invalid.
        """
        with self.assertRaises(ImproperlyConfigured):
            call_command("send_logs", "test@example.com")

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    @patch("django_logging.management.commands.send_logs.shutil.make_archive")
    def test_cleanup_on_failure(
        self, mock_make_archive: Mock, mock_validate_email_settings: Mock
    ) -> None:
        """
        Test that the `send_logs` command cleans up any partially created files when an error occurs
        during the log archiving process.

        Args:
        ----
            mock_make_archive: Mock for the `shutil.make_archive` function, simulating a failure.
            mock_validate_email_settings: Mock for the `validate_email_settings` method in the command.

        Asserts:
        -------
            - The zip file is not left behind if an error occurs during the archiving process.
        """
        temp_log_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        mock_make_archive.side_effect = Exception("Archive failed")

        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            with self.assertRaises(Exception):
                call_command("send_logs", "test@example.com")

        self.assertFalse(os.path.exists(temp_file.name + ".zip"))
        shutil.rmtree(temp_log_dir)
