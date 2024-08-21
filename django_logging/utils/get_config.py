import os
from django.conf import settings

from typing import List
from django_logging.constants import (
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FILE_LEVELS,
    DEFAULT_LOG_DATE_FORMAT,
    DEFAULT_LOG_EMAIL_NOTIFIER,
    DEFAULT_LOG_CONSOLE_LEVEL,
    DEFAULT_LOG_CONSOLE_FORMAT,
    DEFAULT_LOG_CONSOLE_COLORIZE,
    DEFAULT_LOG_FILE_FORMATS,
    DEFAULT_INITIALIZATION_MESSAGE_ENABLE,
    DEFAULT_AUTO_INITIALIZATION_ENABLE,
)


def get_conf() -> List:
    """
    Retrieve logging configuration from Django settings.

    Returns:
        A tuple containing all necessary configurations for logging.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})

    log_levels = log_settings.get("LOG_FILE_LEVELS", DEFAULT_LOG_FILE_LEVELS)
    log_dir = log_settings.get("LOG_DIR", os.path.join(os.getcwd(), DEFAULT_LOG_DIR))
    log_file_formats = log_settings.get("LOG_FILE_FORMATS", DEFAULT_LOG_FILE_FORMATS)
    console_level = log_settings.get("LOG_CONSOLE_LEVEL", DEFAULT_LOG_CONSOLE_LEVEL)
    console_format = log_settings.get("LOG_CONSOLE_FORMAT", DEFAULT_LOG_CONSOLE_FORMAT)
    colorize_console = log_settings.get(
        "LOG_CONSOLE_COLORIZE", DEFAULT_LOG_CONSOLE_COLORIZE
    )
    log_date_format = log_settings.get("LOG_DATE_FORMAT", DEFAULT_LOG_DATE_FORMAT)

    log_email_notifier = log_settings.get(
        "LOG_EMAIL_NOTIFIER", DEFAULT_LOG_EMAIL_NOTIFIER
    )
    log_email_notifier_enable = log_email_notifier.get("ENABLE")
    log_email_notifier_log_levels = [
        "ERROR" if log_email_notifier.get("NOTIFY_ERROR", False) else None,
        "CRITICAL" if log_email_notifier.get("NOTIFY_CRITICAL", False) else None,
    ]
    log_email_notifier_log_format = log_email_notifier.get("LOG_FORMAT")

    configs = [
        log_levels,
        log_dir,
        log_file_formats,
        console_level,
        console_format,
        colorize_console,
        log_date_format,
        log_email_notifier_enable,
        log_email_notifier_log_levels,
        log_email_notifier_log_format,
    ]
    return configs


def use_email_notifier_template() -> bool:
    """
    Check whether the email notifier should use a template based on Django settings.

    Returns:
        bool: True if the email notifier should use a template, False otherwise.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})
    log_email_notifier = log_settings.get(
        "LOG_EMAIL_NOTIFIER", DEFAULT_LOG_EMAIL_NOTIFIER
    )
    return log_email_notifier.get("USE_TEMPLATE", False)


def is_auto_initialization_enabled() -> bool:
    """
    Check if the AUTO_INITIALIZATION_ENABLE for the logging system is set to True in Django settings.

    Returns:
        bool: True if AUTO_INITIALIZATION_ENABLE, False otherwise.
         Defaults to True if not specified.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})
    return log_settings.get(
        "AUTO_INITIALIZATION_ENABLE", DEFAULT_AUTO_INITIALIZATION_ENABLE
    )


def is_initialization_message_enabled() -> bool:
    """
    Check if the INITIALIZATION_MESSAGE_ENABLE is set to True in Django settings.

    Returns:
        bool: True if INITIALIZATION_MESSAGE_ENABLE is True, False otherwise.
         Defaults to True if not specified.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})
    return log_settings.get(
        "INITIALIZATION_MESSAGE_ENABLE", DEFAULT_INITIALIZATION_MESSAGE_ENABLE
    )
