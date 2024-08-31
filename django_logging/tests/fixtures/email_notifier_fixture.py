from typing import Generator, Tuple
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_smtp() -> Generator[MagicMock, None, None]:
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
def email_mock_settings() -> Generator[MagicMock, None, None]:
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
def notifier_mock_logger() -> Generator[Tuple[MagicMock, MagicMock], None, None]:
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
