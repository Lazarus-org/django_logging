import os
from django.conf import settings

from typing import Dict, List, Union, Tuple


def get_conf() -> Tuple[
    List[str], str, Dict[str, Union[int, str]], str, Union[int, str], bool, str, bool, List[str], Union[int, str]
]:
    """
    Retrieve logging configuration from Django settings.

    Returns:
        A tuple containing all necessary configurations for logging.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})

    log_levels = log_settings.get(
        "LOG_FILE_LEVELS", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    log_dir = log_settings.get("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    log_file_formats = log_settings.get("LOG_FILE_FORMATS", {})
    console_level = log_settings.get("LOG_CONSOLE_LEVEL", "DEBUG")
    console_format = log_settings.get("LOG_CONSOLE_FORMAT")
    colorize_console = log_settings.get("LOG_CONSOLE_COLORIZE", True)
    log_date_format = log_settings.get("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")

    log_email_notifier = log_settings.get("LOG_EMAIL_NOTIFIER", {})
    log_email_notifier_enable = log_email_notifier.get("ENABLE", False)
    log_email_notifier_log_levels = [
        "ERROR" if log_email_notifier.get("NOTIFY_ERROR", False) else None,
        "CRITICAL" if log_email_notifier.get("NOTIFY_CRITICAL", False) else None,
    ]
    log_email_notifier_log_format = log_email_notifier.get("LOG_FORMAT")

    return (
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
    )


def use_email_notifier_template() -> bool:
    """
    Check whether the email notifier should use a template based on Django settings.

    Returns:
        bool: True if the email notifier should use a template, False otherwise.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})
    log_email_notifier = log_settings.get("LOG_EMAIL_NOTIFIER", {})
    return log_email_notifier.get("USE_TEMPLATE", True)


def is_initialization_message_enabled() -> bool:
    """
    Check if the initialization message for the logging system is enabled in Django settings.

    Returns:
        bool: True if an initialization message is specified, False otherwise. Defaults to True if not specified.
    """
    log_settings = getattr(settings, "DJANGO_LOGGING", {})
    return log_settings.get("INITIALIZATION_MESSAGE", True)

