import sys
import threading
from smtplib import SMTPException
from typing import Tuple
from unittest.mock import ANY, MagicMock

import pytest

from django_logging.utils.log_email_notifier.notifier import send_email_async
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_email_notifier,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestEmailNotifier:

    def test_send_email_async_success(
        self,
        mock_smtp: MagicMock,
        email_mock_settings: MagicMock,
        notifier_mock_logger: Tuple[MagicMock, MagicMock],
    ) -> None:
        """
        Test that the send_email_async function successfully sends an email.

        This test verifies that when `send_email_async` is called with valid parameters:
        - The SMTP server is correctly initialized with the specified host and port.
        - The login method is called with the correct credentials.
        - The email is sent with the expected 'From', 'To', 'Subject', and 'Body' fields.
        - The SMTP connection is properly terminated with a call to `quit`.
        - The success log message is correctly written.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.notifier.SMTP` to simulate SMTP interactions.
        - `django_logging.utils.log_email_notifier.notifier.settings` to provide mock email settings.
        - `django_logging.utils.log_email_notifier.notifier.logger.info` and `logger.warning` to test logging behavior.

        Asserts:
        -------
        - The `SMTP` object was called with the correct host and port.
        - The `login` method was called with the correct credentials.
        - The `sendmail` method was called with the correct email fields.
        - The `quit` method was called on the SMTP instance.
        - The success message was logged and no warning message was logged.
        """
        mock_info, mock_warning = notifier_mock_logger

        email_sent_event = threading.Event()

        send_email_async(
            "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
        )

        email_sent_event.wait()

        mock_smtp.assert_called_once_with(
            email_mock_settings.EMAIL_HOST, email_mock_settings.EMAIL_PORT
        )
        mock_smtp_instance = mock_smtp.return_value

        mock_smtp_instance.login.assert_called_once_with(
            email_mock_settings.EMAIL_HOST_USER, email_mock_settings.EMAIL_HOST_PASSWORD
        )

        sendmail_args = mock_smtp_instance.sendmail.call_args[0]

        expected_from = email_mock_settings.DEFAULT_FROM_EMAIL
        expected_to = ["to@example.com"]
        expected_subject = "Test Subject"
        expected_body = "Test Body"

        assert sendmail_args[0] == expected_from
        assert sendmail_args[1] == expected_to

        actual_email_content = sendmail_args[2]
        assert f"Subject: {expected_subject}" in actual_email_content
        assert expected_body in actual_email_content

        mock_smtp_instance.quit.assert_called_once()

        mock_info.assert_called_once_with(
            "Log Record has been sent to ADMIN EMAIL successfully."
        )
        mock_warning.assert_not_called()

    def test_send_email_async_failure(
        self,
        mock_smtp: MagicMock,
        email_mock_settings: MagicMock,
        notifier_mock_logger: Tuple[MagicMock, MagicMock],
    ) -> None:
        """
        Test that the send_email_async function handles SMTP failures.

        This test verifies that when `send_email_async` encounters an SMTP exception:
        - The failure is logged with an appropriate error message.
        - The success message is not logged.

        Mocks:
        ------
        - `django_logging.utils.log_email_notifier.notifier.SMTP` to simulate an SMTP failure.

        Asserts:
        -------
        - The warning message was logged indicating the failure.
        - The success message was not logged.
        """
        mock_info, mock_warning = notifier_mock_logger
        mock_smtp.side_effect = SMTPException("SMTP failure")

        email_sent_event = threading.Event()

        send_email_async(
            "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
        )

        email_sent_event.wait()

        mock_warning.assert_called_once_with(
            "Email Notifier failed to send Log Record: %s", ANY
        )
        mock_info.assert_not_called()
