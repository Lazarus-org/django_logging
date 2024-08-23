import logging
import pytest
import threading
from unittest.mock import patch, MagicMock
from django_logging.utils.log_email_notifier.notifier import send_email_async


@pytest.fixture
def mock_smtp() -> MagicMock:
    """
    Fixture to mock the SMTP object used for sending emails.

    This fixture patches the `SMTP` class from `smtplib` to prevent actual email sending and
    allows testing the interactions with the mock SMTP object.

    Yields:
    -------
    unittest.mock.MagicMock
        A mock object representing the SMTP class.
    """
    with patch("django_logging.utils.log_email_notifier.notifier.SMTP") as mock_smtp:
        yield mock_smtp


@pytest.fixture
def mock_settings() -> MagicMock:
    """
    Fixture to mock the Django settings used for email configuration.

    This fixture patches the `settings` object to provide fake email configuration values
    without needing to access the actual Django settings.

    Yields:
    -------
    unittest.mock.MagicMock
        A mock object representing the Django settings with predefined email configurations.
    """
    with patch(
        "django_logging.utils.log_email_notifier.notifier.settings"
    ) as mock_settings:
        mock_settings.DEFAULT_FROM_EMAIL = "from@example.com"
        mock_settings.EMAIL_HOST = "smtp.example.com"
        mock_settings.EMAIL_PORT = 587
        mock_settings.EMAIL_HOST_USER = "user@example.com"
        mock_settings.EMAIL_HOST_PASSWORD = "password"
        yield mock_settings


@pytest.fixture
def mock_logger() -> tuple[MagicMock, MagicMock]:
    """
    Fixture to mock the logger used for logging messages.

    This fixture patches the `logger.info` and `logger.warning` methods to intercept and test
    logging calls without affecting the actual logging configuration.

    Yields:
    -------
    tuple
        A tuple containing mock objects for `logger.info` and `logger.warning`.
    """
    with patch(
        "django_logging.utils.log_email_notifier.notifier.logger.info"
    ) as mock_info, patch(
        "django_logging.utils.log_email_notifier.notifier.logger.warning"
    ) as mock_warning:
        yield mock_info, mock_warning


def test_send_email_async_success(
    mock_smtp: MagicMock,
    mock_settings: MagicMock,
    mock_logger: tuple[MagicMock, MagicMock],
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
    mock_info, mock_warning = mock_logger

    email_sent_event = threading.Event()

    send_email_async(
        "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
    )

    email_sent_event.wait()

    mock_smtp.assert_called_once_with(
        mock_settings.EMAIL_HOST, mock_settings.EMAIL_PORT
    )
    mock_smtp_instance = mock_smtp.return_value

    mock_smtp_instance.login.assert_called_once_with(
        mock_settings.EMAIL_HOST_USER, mock_settings.EMAIL_HOST_PASSWORD
    )

    sendmail_args = mock_smtp_instance.sendmail.call_args[0]

    expected_from = mock_settings.DEFAULT_FROM_EMAIL
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
    mock_smtp: MagicMock,
    mock_settings: MagicMock,
    mock_logger: tuple[MagicMock, MagicMock],
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
    mock_info, mock_warning = mock_logger
    mock_smtp.side_effect = Exception("SMTP failure")

    email_sent_event = threading.Event()

    send_email_async(
        "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
    )

    email_sent_event.wait()

    mock_warning.assert_called_once_with(
        "Email Notifier failed to send Log Record: SMTP failure"
    )
    mock_info.assert_not_called()
