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
