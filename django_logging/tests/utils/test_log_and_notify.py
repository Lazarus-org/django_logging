import logging
import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin


# Helper function to mock LogConfig
def mock_log_config(email_notifier_enable=True):
    """
    Helper function to create a mock LogConfig object.

    Parameters:
    -----------
    email_notifier_enable : bool
        Indicates whether the email notifier is enabled.

    Returns:
    --------
    MagicMock
        A mock object with specified settings.
    """
    return MagicMock(
        log_email_notifier_enable=email_notifier_enable,
        log_email_notifier_log_format=1,
    )


@pytest.fixture
def mock_logger():
    """
    Fixture to create a mock logger object for testing.

    Returns:
    --------
    MagicMock
        A mock logger object used in the tests.
    """
    return MagicMock()


@pytest.fixture
def mock_settings():
    """
    Fixture to mock Django settings related to email notifications.

    This fixture sets up a mock ADMIN_EMAIL setting for testing and cleans up
    by deleting the setting after the test.

    Yields:
    -------
    None
    """
    settings.ADMIN_EMAIL = "admin@example.com"
    yield
    del settings.ADMIN_EMAIL


def test_log_and_notify_email_notifier_disabled(mock_logger):
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
        return_value=mock_log_config(False),
    ):
        with pytest.raises(ValueError, match="Email notifier is disabled"):
            log_and_notify_admin(mock_logger, logging.ERROR, "Test message")


def test_log_and_notify_admin_success(mock_logger, mock_settings):
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
        return_value=mock_log_config(True),
    ):
        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
        ) as mock_frame:
            mock_frame.return_value.f_back = MagicMock(
                f_code=MagicMock(co_filename="file.py", co_name="function"),
                f_lineno=42,
            )

            with patch.object(mock_logger, "makeRecord", return_value=log_record):
                with patch(
                    "django_logging.utils.log_email_notifier.log_and_notify.EmailHandler.render_template",
                    return_value="Formatted email body",
                ):
                    with patch(
                        "django_logging.utils.log_email_notifier.log_and_notify.send_email_async"
                    ) as mock_send_email:
                        log_and_notify_admin(mock_logger, logging.ERROR, "Test message")

                        # Ensure the log was handled
                        mock_logger.handle.assert_called_once_with(log_record)

                        # Ensure email was sent
                        mock_send_email.assert_called_once_with(
                            "New Log Record: ERROR",
                            "Formatted email body",
                            ["admin@example.com"],
                        )


def test_log_and_notify_admin_logging_failure(mock_logger, mock_settings):
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
        return_value=mock_log_config(True),
    ):
        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
        ) as mock_frame:
            mock_frame.return_value.f_back = MagicMock(
                f_code=MagicMock(co_filename="file.py", co_name="function"),
                f_lineno=42,
            )

            # Simulate an error during logger.makeRecord
            mock_logger.makeRecord.side_effect = TypeError("Invalid parameter")

            with pytest.raises(
                ValueError, match="Failed to log message due to invalid param"
            ):
                log_and_notify_admin(mock_logger, logging.ERROR, "Test message")


def test_log_and_notify_admin_missing_admin_email(mock_logger):
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
        return_value=mock_log_config(True),
    ):
        with patch(
            "django_logging.utils.log_email_notifier.log_and_notify.inspect.currentframe"
        ) as mock_frame:
            mock_frame.return_value.f_back = MagicMock(
                f_code=MagicMock(co_filename="file.py", co_name="function"),
                f_lineno=42,
            )

            with patch.object(mock_logger, "makeRecord", return_value=log_record):
                with patch(
                    "django_logging.utils.log_email_notifier.log_and_notify.EmailHandler.render_template",
                    return_value="Formatted email body",
                ):
                    with pytest.raises(ValueError) as exc_info:
                        log_and_notify_admin(mock_logger, logging.ERROR, "Test message")

                    assert (
                        str(exc_info.value)
                        == "'ADMIN EMAIL' not provided, please provide 'ADMIN_EMAIL' in your settings"
                    )
