import os

from django.core.exceptions import ImproperlyConfigured

from django_logging.constants.settings_types import (
    LOG_LEVELS_TYPE, LOG_DIR_TYPE, LogFileFormatsType,
    LOG_CONSOLE_LEVEL_TYPE, LOG_CONSOLE_FORMAT_TYPE,
    LOG_CONSOLE_COLORIZE_TYPE, LOG_DATE_FORMAT_TYPE, FormatOption,
)
from django_logging.settings.conf import LogConfig, LogManager

from typing import List
from django_logging.constants.ansi_colors import AnsiColors
from django_logging.utils.get_config import is_auto_initialization_enabled, is_initialization_message_enabled


def set_logging(
    log_levels: LOG_LEVELS_TYPE,
    log_dir: LOG_DIR_TYPE,
    log_file_formats: LogFileFormatsType,
    console_level: LOG_CONSOLE_LEVEL_TYPE,
    console_format: LOG_CONSOLE_FORMAT_TYPE,
    colorize_console: LOG_CONSOLE_COLORIZE_TYPE,
    log_date_format: LOG_DATE_FORMAT_TYPE,
    log_email_notifier_enable: bool,
    log_email_notifier_log_levels: LOG_LEVELS_TYPE,
    log_email_notifier_log_format: FormatOption,
) -> None:
    """
    Sets up the logging configuration.

    Args:
        log_levels (List[str]): A list of log levels to configure.
        log_dir (str): The directory where log files will be stored.
    """
    if not is_auto_initialization_enabled():
        return

    try:
        log_config = LogConfig(
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

        log_manager = LogManager(log_config)
        log_manager.create_log_files()
        log_manager.set_conf()
    except (ValueError, ImproperlyConfigured, AttributeError):
        import logging

        logging.warning(
            "\n"
            f"========================{AnsiColors.RED_BACKGROUND}DJANGO LOGGING{AnsiColors.RESET}"
            f"========================\n"
            f"{AnsiColors.RED}[CONFIGURATION ERROR]{AnsiColors.RESET}"
            f" A configuration issue has been detected.\n"
            "System checks will be run to provide more detailed information.\n"
            "==============================================================\n"
        )
        return

    if os.environ.get("RUN_MAIN") == "true":
        if is_initialization_message_enabled():
            from logging import getLogger

            logger = getLogger(__name__)
            logger.info(
                "Logging initialized with the following configurations:\n"
                "Log File levels: %s.\n"
                "Log files are being written to: %s.\n"
                "Console output level: %s.\n"
                "Colorize console: %s.\n"
                "Log date format: %s.\n"
                "Email notifier enabled: %s.\n",
                log_levels,
                log_dir,
                console_level or "default (DEBUG)",
                colorize_console,
                log_date_format,
                log_email_notifier_enable,
            )
