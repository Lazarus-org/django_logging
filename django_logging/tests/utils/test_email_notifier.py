import logging
import pytest
import threading
from unittest.mock import patch, MagicMock
from django_logging.utils.log_email_notifier.notifier import send_email_async


@pytest.fixture
def mock_smtp():
    with patch("django_logging.utils.log_email_notifier.notifier.SMTP") as mock_smtp:
        yield mock_smtp


@pytest.fixture
def mock_settings():
    with patch("django_logging.utils.log_email_notifier.notifier.settings") as mock_settings:
        mock_settings.DEFAULT_FROM_EMAIL = "from@example.com"
        mock_settings.EMAIL_HOST = "smtp.example.com"
        mock_settings.EMAIL_PORT = 587
        mock_settings.EMAIL_HOST_USER = "user@example.com"
        mock_settings.EMAIL_HOST_PASSWORD = "password"
        yield mock_settings


@pytest.fixture
def mock_logger():
    with patch("django_logging.utils.log_email_notifier.notifier.logger.info") as mock_info, patch(
        "django_logging.utils.log_email_notifier.notifier.logger.warning"
    ) as mock_warning:
        yield mock_info, mock_warning


# Test for successful email sending
def test_send_email_async_success(mock_smtp, mock_settings, mock_logger):
    mock_info, mock_warning = mock_logger

    # Create an event to signal when the email has been sent
    email_sent_event = threading.Event()

    # Pass the event to the send_email_async function
    send_email_async(
        "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
    )

    # Wait for the event to be set, indicating the email was sent
    email_sent_event.wait()

    # Ensure the SMTP server was called with the correct parameters
    mock_smtp.assert_called_once_with(
        mock_settings.EMAIL_HOST, mock_settings.EMAIL_PORT
    )
    mock_smtp_instance = mock_smtp.return_value

    # Check if login was called with the correct credentials
    mock_smtp_instance.login.assert_called_once_with(
        mock_settings.EMAIL_HOST_USER, mock_settings.EMAIL_HOST_PASSWORD
    )

    # Capture the arguments passed to sendmail
    sendmail_args = mock_smtp_instance.sendmail.call_args[0]

    # Verify the email content
    expected_from = mock_settings.DEFAULT_FROM_EMAIL
    expected_to = ["to@example.com"]
    expected_subject = "Test Subject"
    expected_body = "Test Body"

    # Check that the 'From' and 'To' fields are correct
    assert sendmail_args[0] == expected_from
    assert sendmail_args[1] == expected_to

    # Parse the actual email content and compare it to the expected content
    actual_email_content = sendmail_args[2]
    assert f"Subject: {expected_subject}" in actual_email_content
    assert expected_body in actual_email_content

    # Check if the SMTP server was properly quit
    mock_smtp_instance.quit.assert_called_once()

    # Ensure the success log message was written
    mock_info.assert_called_once_with(
        "Log Record has been sent to ADMIN EMAIL successfully."
    )
    mock_warning.assert_not_called()


def test_send_email_async_failure(mock_smtp, mock_settings, mock_logger):
    mock_info, mock_warning = mock_logger
    mock_smtp.side_effect = Exception("SMTP failure")

    email_sent_event = threading.Event()

    send_email_async(
        "Test Subject", "Test Body", ["to@example.com"], event=email_sent_event
    )

    email_sent_event.wait()

    # Ensure the failure log message was written
    mock_warning.assert_called_once_with(
        "Email Notifier failed to send Log Record: SMTP failure"
    )
    mock_info.assert_not_called()
