import logging
import inspect
from typing import Optional, Dict

from django.conf import settings

from django_logging.utils.email import send_email_async
from django_logging.handlers import EmailHandler


def log_and_notify(logger, level: int, message: str, extra: Optional[Dict] = None):
    # Get the caller's frame to capture the correct module, file, and line number
    frame = inspect.currentframe().f_back

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

    request = extra.get("request") if extra else None

    # Render the email template with the formatted message
    email_body = EmailHandler.render_template(log_record, request)

    subject = f"New Log Record: {logging.getLevelName(level)}"
    send_email_async(subject, email_body, [settings.ADMIN_EMAIL])
