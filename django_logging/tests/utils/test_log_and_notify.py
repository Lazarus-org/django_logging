import logging
import sys
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_log_and_notify,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestLogAndNotify:
    def mock_log_config(self, email_notifier_enable: bool = True) -> Dict:
        """
        Helper function to create a mock LogConfig object.

        Parameters:
        -----------
        email_notifier_enable : bool
            Indicates whether the email notifier is enabled.

        Returns:
        --------
        Dict
            A dictionary with the specified settings.
        """
        return {
            "log_email_notifier_enable": email_notifier_enable,
            "log_email_notifier_log_format": 1,
        }

    def test_log_and_notify_email_notifier_disabled(
        self, magic_mock_logger: MagicMock
    ) -> None:
        """
        Test that a ValueError is raised when email notifier is disabled.

        This test checks that the `log_and_notify_admin` function raises a `ValueError`
        if the email notifier is disabled in the configuration.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.log_and_notify.get_config` to return a
          configuration where the email notifier is disabled.

        Asserts:
        -------
        - A `ValueError` with the message "Email notifier is disabled" is raised.
        """
        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.get_config",
            return_value=self.mock_log_config(False),
        ):
            with pytest.raises(ValueError, match="Email notifier is disabled"):
                log_and_notify_admin(magic_mock_logger, logging.ERROR, "Test message")

    def test_log_and_notify_admin_success(
        self, magic_mock_logger: MagicMock, admin_email_mock_settings: None
    ) -> None:
        """
        Test successful logging and email notification to admin.

        This test verifies that the `log_and_notify_admin` function correctly handles a log
        record and sends an email notification when the email notifier is enabled.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.log_and_notify.get_config` to return a
          configuration where the email notifier is enabled.
        - `django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe` to
          simulate the current frame information.
        - `mock_logger.makeRecord` to simulate creating a log record.
        - `EmailHandler.render_template` to provide a mock email body.
        - `send_email_async` to check the email sending functionality.

        Asserts:
        -------
        - The log record is handled by the logger.
        - An email is sent with the expected subject and body.
        """
        log_record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="file.py",
            lineno=42,
            msg="Test message",
            args=None,
            exc_info=None,
        )

        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.get_config",
            return_value=self.mock_log_config(True),
        ):
            with patch(
                "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
            ) as mock_frame:
                mock_frame.return_value.f_back = MagicMock(
                    f_code=MagicMock(co_filename="file.py", co_name="function"),
                    f_lineno=42,
                )

                with patch.object(
                    magic_mock_logger, "makeRecord", return_value=log_record
                ):
                    with patch(
                        "django_logging.utils.log_email_notifier.log_and_notify.EmailHandler.render_template",
                        return_value="Formatted email body",
                    ):
                        with patch(
                            "django_logging.utils.log_email_notifier.log_and_notify.send_email_async"
                        ) as mock_send_email:
                            log_and_notify_admin(
                                magic_mock_logger, logging.ERROR, "Test message"
                            )

                            # Ensure the log was handled
                            magic_mock_logger.handle.assert_called_once_with(log_record)

                            # Ensure email was sent
                            mock_send_email.assert_called_once_with(
                                "New Log Record: ERROR",
                                "Formatted email body",
                                ["admin@example.com"],
                            )

    def test_log_and_notify_admin_logging_failure(
        self, magic_mock_logger: MagicMock, admin_email_mock_settings: None
    ) -> None:
        """
        Test logging failure due to invalid parameters.

        This test verifies that the `log_and_notify_admin` function raises a `ValueError`
        if there is an error during the creation of the log record.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.log_and_notify.get_config` to return a
          configuration where the email notifier is enabled.
        - `django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe` to
          simulate the current frame information.
        - Simulates a `TypeError` during `mock_logger.makeRecord`.

        Asserts:
        -------
        - A `ValueError` with the message "Failed to log message due to invalid param" is raised.
        """
        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.get_config",
            return_value=self.mock_log_config(True),
        ):
            with patch(
                "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
            ) as mock_frame:
                mock_frame.return_value.f_back = MagicMock(
                    f_code=MagicMock(co_filename="file.py", co_name="function"),
                    f_lineno=42,
                )

                # Simulate an error during logger.makeRecord
                magic_mock_logger.makeRecord.side_effect = TypeError(
                    "Invalid parameter"
                )

                with pytest.raises(
                    ValueError, match="Failed to log message due to invalid param"
                ):
                    log_and_notify_admin(
                        magic_mock_logger, logging.ERROR, "Test message"
                    )

    def test_log_and_notify_admin_missing_admin_email(
        self, magic_mock_logger: MagicMock
    ) -> None:
        """
        Test logging and email notification when ADMIN_EMAIL is missing.

        This test verifies that the `log_and_notify_admin` function raises a `ValueError`
        if the `ADMIN_EMAIL` setting is not provided.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.log_and_notify.get_config` to return a
          configuration where the email notifier is enabled.
        - `django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe` to
          simulate the current frame information.
        - `mock_logger.makeRecord` to simulate creating a log record.

        Asserts:
        -------
        - A `ValueError` with the message "'ADMIN EMAIL' not provided, please provide 'ADMIN_EMAIL' in your settings" is raised.
        """
        # Simulate the absence of ADMIN_EMAIL in settings
        settings.ADMIN_EMAIL = None

        log_record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="file.py",
            lineno=42,
            msg="Test message",
            args=None,
            exc_info=None,
        )

        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.get_config",
            return_value=self.mock_log_config(True),
        ):
            with patch(
                "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
            ) as mock_frame:
                mock_frame.return_value.f_back = MagicMock(
                    f_code=MagicMock(co_filename="file.py", co_name="function"),
                    f_lineno=42,
                )

                with patch.object(
                    magic_mock_logger, "makeRecord", return_value=log_record
                ):
                    with patch(
                        "django_logging.utils.log_email_notifier.log_and_notify.EmailHandler.render_template",
                        return_value="Formatted email body",
                    ):
                        with pytest.raises(ValueError) as exc_info:
                            log_and_notify_admin(
                                magic_mock_logger, logging.ERROR, "Test message"
                            )

                        assert (
                            str(exc_info.value)
                            == "'ADMIN EMAIL' not provided, please provide 'ADMIN_EMAIL' in your settings"
                        )
