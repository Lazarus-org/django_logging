import os
import tempfile
import shutil

from unittest.mock import patch, ANY

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import TestCase


class SendLogsCommandTests(TestCase):

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    @patch("django_logging.management.commands.send_logs.shutil.make_archive")
    @patch("django_logging.management.commands.send_logs.EmailMessage")
    def test_handle_success(
        self, mock_email_message, mock_make_archive, mock_validate_email_settings
    ):
        # Setup
        temp_log_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        mock_make_archive.return_value = temp_file.name

        # Mock settings
        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            # Execute command
            call_command("send_logs", "test@example.com")

        # Assert
        mock_validate_email_settings.assert_called_once()
        mock_make_archive.assert_called_once_with(ANY, "zip", temp_log_dir)
        mock_email_message.assert_called_once()

        # Cleanup
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
        self, mock_email_send, mock_validate_email_settings
    ):
        # Setup
        temp_log_dir = tempfile.mkdtemp()
        mock_email_send.side_effect = Exception("Email send failed")

        # Mock settings
        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            with self.assertLogs(
                "django_logging.management.commands.send_logs", level="ERROR"
            ) as cm:
                call_command("send_logs", "test@example.com")

        # Assert
        self.assertIn(
            "ERROR:django_logging.management.commands.send_logs:Failed to send logs: Email send failed",
            cm.output,
        )

        # Cleanup
        shutil.rmtree(temp_log_dir)

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    def test_handle_missing_log_dir(self, mock_validate_email_settings):
        # Mock settings with a non-existent log directory
        non_existent_dir = "/non/existent/directory"
        with self.settings(DJANGO_LOGGING={"LOG_DIR": non_existent_dir}):
            with self.assertLogs(
                "django_logging.management.commands.send_logs", level="ERROR"
            ) as cm:
                # Call the command and check that no exception is raised but logs are captured
                call_command("send_logs", "test@example.com")

            # Check if the correct error message is logged
            self.assertIn(
                f'ERROR:django_logging.management.commands.send_logs:Log directory "{non_existent_dir}" does not exist.',
                cm.output,
            )

            # Check that validate_email_settings was not called
        mock_validate_email_settings.assert_not_called()

    @patch(
        "django_logging.management.commands.send_logs.check_email_settings",
        return_value=None,
    )
    def test_validate_email_settings_success(self, mock_check_email_settings):
        call_command("send_logs", "test@example.com")
        mock_check_email_settings.assert_called_once()

    @patch(
        "django_logging.management.commands.send_logs.check_email_settings",
        return_value="Missing config",
    )
    def test_validate_email_settings_failure(self, mock_check_email_settings):
        with self.assertRaises(ImproperlyConfigured):
            call_command("send_logs", "test@example.com")

    @patch(
        "django_logging.management.commands.send_logs.Command.validate_email_settings"
    )
    @patch("django_logging.management.commands.send_logs.shutil.make_archive")
    def test_cleanup_on_failure(self, mock_make_archive, mock_validate_email_settings):
        # Setup
        temp_log_dir = tempfile.mkdtemp()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        mock_make_archive.side_effect = Exception("Archive failed")

        # Mock settings
        with self.settings(DJANGO_LOGGING={"LOG_DIR": temp_log_dir}):
            with self.assertRaises(Exception):
                call_command("send_logs", "test@example.com")

        # Assert
        self.assertFalse(os.path.exists(temp_file.name + ".zip"))

        # Cleanup
        shutil.rmtree(temp_log_dir)
