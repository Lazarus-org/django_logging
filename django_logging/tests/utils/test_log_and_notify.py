import logging
import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin


# Helper function to mock LogConfig
def mock_log_config(email_notifier_enable=True):
    return MagicMock(
        log_email_notifier_enable=email_notifier_enable,
        log_email_notifier_log_format=1,
    )


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def mock_settings():
    settings.ADMIN_EMAIL = "admin@example.com"
    yield
    del settings.ADMIN_EMAIL


# Test: Email notifier is disabled
def test_log_and_notify_email_notifier_disabled(mock_logger):
    with patch(
        "django_logging.utils.log_email_notifier.log_and_notify.get_config",
        return_value=mock_log_config(False),
    ):
        with pytest.raises(ValueError, match="Email notifier is disabled"):
            log_and_notify_admin(mock_logger, logging.ERROR, "Test message")


# Test: Successful log and email notification to admin
def test_log_and_notify_admin_success(mock_logger, mock_settings):
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


# Test: Logging failure due to invalid parameters
def test_log_and_notify_admin_logging_failure(mock_logger, mock_settings):
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


# Test: Missing ADMIN_EMAIL setting
def test_log_and_notify_admin_missing_admin_email(mock_logger):
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
