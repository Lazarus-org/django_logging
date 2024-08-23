import logging
import pytest
from unittest.mock import patch, MagicMock, ANY

from django.conf import settings

from django_logging.handlers.email_handler import EmailHandler


@pytest.fixture
def log_record() -> logging.LogRecord:
    """
    Fixture to create a dummy log record.

    Returns:
    -------
    logging.LogRecord
        A dummy log record with predefined attributes for testing.
    """
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
def email_handler() -> EmailHandler:
    """
    Fixture to create an EmailHandler instance.

    Returns:
    -------
    EmailHandler
        An instance of the EmailHandler class.
    """
    return EmailHandler()


@patch("django_logging.handlers.email_handler.send_email_async")
@patch("django_logging.handlers.email_handler.EmailHandler.render_template")
@patch(
    "django_logging.handlers.email_handler.use_email_notifier_template",
    return_value=True,
)
def test_emit_with_html_template(
    mock_use_template: MagicMock, mock_render_template: MagicMock, mock_send_email: MagicMock, email_handler: EmailHandler, log_record: logging.LogRecord
) -> None:
    """
    Test the emit method when HTML templates are used.

    This test verifies that the EmailHandler's `emit` method correctly renders an HTML
    template and sends an email when `use_email_notifier_template` is enabled.

    Args:
    ----
    mock_use_template : MagicMock
        Mock for the `use_email_notifier_template` function.
    mock_render_template : MagicMock
        Mock for the `render_template` method.
    mock_send_email : MagicMock
        Mock for the `send_email_async` function.
    email_handler : EmailHandler
        The EmailHandler instance being tested.
    log_record : logging.LogRecord
        The log record fixture used for testing.

    Asserts:
    -------
    - `render_template` is called once with the correct arguments.
    - `send_email_async` is called once with the expected email subject, HTML content, and recipients.
    """
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
def test_emit_without_html_template(mock_use_template: MagicMock, mock_send_email: MagicMock, log_record: logging.LogRecord) -> None:
    """
    Test the emit method when HTML templates are not used.

    This test checks that the EmailHandler's `emit` method correctly sends a plain text
    email when `use_email_notifier_template` is disabled.

    Args:
    ----
    mock_use_template : MagicMock
        Mock for the `use_email_notifier_template` function.
    mock_send_email : MagicMock
        Mock for the `send_email_async` function.
    log_record : logging.LogRecord
        The log record fixture used for testing.

    Asserts:
    -------
    - `send_email_async` is called once with the expected email subject, plain text content, and recipients.
    """
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
    mock_send_email: MagicMock, mock_handle_error: MagicMock, email_handler: EmailHandler, log_record: logging.LogRecord
) -> None:
    """
    Test that the emit method handles exceptions during email sending.

    This test ensures that when an exception occurs during the email sending process,
    the `handleError` method is called to manage the error.

    Args:
    ----
    mock_send_email : MagicMock
        Mock for the `send_email_async` function.
    mock_handle_error : MagicMock
        Mock for the `handleError` method.
    email_handler : EmailHandler
        The EmailHandler instance being tested.
    log_record : logging.LogRecord
        The log record fixture used for testing.

    Asserts:
    -------
    - `handleError` is called once with the log record when an exception occurs.
    """
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
def test_render_template(mock_engines: MagicMock, mock_get_user_agent: MagicMock, mock_get_ip_address: MagicMock):
    """
    Test the render_template method of EmailHandler.

    This test verifies that the `render_template` method correctly renders the HTML
    template with the provided log message and request details.

    Args:
    ----
    mock_engines : MagicMock
        Mock for the Django template engines.
    mock_get_user_agent : MagicMock
        Mock for the `get_user_agent` method of the middleware.
    mock_get_ip_address : MagicMock
        Mock for the `get_ip_address` method of the middleware.

    Asserts:
    -------
    - The correct template is retrieved and rendered with the expected context data.
    - The rendered HTML output matches the expected formatted log.

    Returns:
    -------
    str
        The rendered HTML output for the log message.
    """
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
