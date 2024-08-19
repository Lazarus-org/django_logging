import logging
import inspect
from typing import Optional, Dict

from django.conf import settings

from django_logging.constants.format_options import FORMAT_OPTIONS
from django_logging.utils.email import send_email_async
from django_logging.handlers import EmailHandler
from django_logging.settings.conf import LogConfig


def log_and_notify(logger, level: int, message: str, extra: Optional[Dict] = None) -> None:
    # Get the caller's frame to capture the correct module, file, and line number
    frame = inspect.currentframe().f_back

    if not hasattr(settings, "DJANGO_LOGGING"):
        raise ValueError(
            "Email notifier is disabled. Please add DJANGO_LOGGING to your settings file and set "
            "the 'ENABLE' option to True in the 'LOG_EMAIL_NOTIFIER' settings to activate email notifications."
        )
    email_notifier_conf = settings.DJANGO_LOGGING.get("LOG_EMAIL_NOTIFIER")

    notifier_enable = email_notifier_conf.get("ENABLE", False)
    if not notifier_enable:
        raise ValueError(
            "Email notifier is disabled. Please set the 'ENABLE' option to True in the 'LOG_EMAIL_NOTIFIER' "
            "settings to activate email notifications."
        )

    _format = email_notifier_conf.get("LOG_FORMAT", FORMAT_OPTIONS[1])

    try:
        # create a LogRecord
        log_record = logger.makeRecord(
            name=logger.name,
            level=level,
            fn=frame.f_code.co_filename,
            lno=frame.f_lineno,
            msg=message,
            args=None,
            exc_info=None,
            func=frame.f_code.co_name,
            extra=extra,
        )

        # Pass the LogRecord to the logger's handlers
        logger.handle(log_record)
    except TypeError as e:
        raise ValueError(
            f"Failed to log message due to invalid param. Original error: {e}"
        )
    # Create a formatter instance and pass the email_notifier format
    formatter = logging.Formatter(LogConfig.resolve_format(_format))

    # Format the log message using the formatter
    formatted_message = formatter.format(log_record)

    request = extra.get("request") if extra else None

    # Render the email template with the formatted message
    email_body = EmailHandler.render_template(formatted_message, request)

    subject = f"New Log Record: {logging.getLevelName(level)}"
    send_email_async(subject, email_body, [settings.ADMIN_EMAIL])
