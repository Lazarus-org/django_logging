import logging
import pytest
from unittest.mock import patch, MagicMock, ANY

from django.conf import settings

from django_logging.handlers.email_handler import EmailHandler


@pytest.fixture
def log_record():
    """Fixture to create a dummy log record."""
    return logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )


@pytest.fixture
def email_handler():
    """Fixture to create an EmailHandler instance."""
    return EmailHandler()


@patch("django_logging.handlers.email_handler.send_email_async")
@patch("django_logging.handlers.email_handler.EmailHandler.render_template")
@patch(
    "django_logging.handlers.email_handler.use_email_notifier_template",
    return_value=True,
)
def test_emit_with_html_template(
    mock_use_template, mock_render_template, mock_send_email, email_handler, log_record
):
    """Test the emit method with HTML template."""
    mock_render_template.return_value = "<html>Formatted Log</html>"

    email_handler.emit(log_record)

    mock_render_template.assert_called_once_with("Test message", None)
    mock_send_email.assert_called_once_with(
        "New Log Record: ERROR", "<html>Formatted Log</html>", [settings.ADMIN_EMAIL]
    )


@patch("django_logging.handlers.email_handler.send_email_async")
@patch(
    "django_logging.handlers.email_handler.use_email_notifier_template",
    return_value=False,
)
def test_emit_without_html_template(mock_use_template, mock_send_email, log_record):
    """Test the emit method without HTML template."""
    email_handler = EmailHandler()
    email_handler.emit(log_record)

    mock_send_email.assert_called_once_with(
        "New Log Record: ERROR", "Test message", [settings.ADMIN_EMAIL]
    )


@patch("django_logging.handlers.email_handler.EmailHandler.handleError")
@patch(
    "django_logging.handlers.email_handler.send_email_async",
    side_effect=Exception("Email send failed"),
)
def test_emit_handles_exception(
    mock_send_email, mock_handle_error, email_handler, log_record
):
    """Test that emit handles exceptions properly."""
    email_handler.emit(log_record)

    mock_handle_error.assert_called_once_with(log_record)


@patch(
    "django_logging.handlers.email_handler.RequestLogMiddleware.get_ip_address",
    return_value="127.0.0.1",
)
@patch(
    "django_logging.handlers.email_handler.RequestLogMiddleware.get_user_agent",
    return_value="Mozilla/5.0",
)
@patch("django_logging.handlers.email_handler.engines")
def test_render_template(mock_engines, mock_get_user_agent, mock_get_ip_address):
    """Test the render_template method."""
    mock_template = MagicMock()
    mock_template.render.return_value = "<html>Formatted Log</html>"
    mock_django_engine = MagicMock()
    mock_django_engine.get_template.return_value = mock_template
    mock_engines.__getitem__.return_value = mock_django_engine

    email_handler = EmailHandler()

    mock_request = MagicMock()
    rendered_output = email_handler.render_template("Test message", mock_request)

    mock_django_engine.get_template.assert_called_once_with(
        "email_notifier_template.html"
    )
    mock_template.render.assert_called_once_with(
        {
            "message": "Test message",
            "time": ANY,  # The actual time is not critical to the test
            "browser_type": "Mozilla/5.0",
            "ip_address": "127.0.0.1",
        }
    )
    assert rendered_output == "<html>Formatted Log</html>"
