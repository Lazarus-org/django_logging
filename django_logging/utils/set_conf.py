import os

from django.core.exceptions import ImproperlyConfigured

from django_logging.constants.ansi_colors import AnsiColors
from django_logging.constants.config_types import (
    FormatOption,
    LogDateFormat,
    LogDir,
    LogFileFormatsType,
    LogLevel,
    LogLevels,
    NotifierLogLevels,
)
from django_logging.settings.conf import LogConfig, LogManager
from django_logging.utils.get_conf import (
    is_auto_initialization_enabled,
    is_initialization_message_enabled,
)


# pylint: disable=too-many-arguments, too-many-locals
def set_config(
    log_levels: LogLevels,
    log_dir: LogDir,
    log_file_formats: LogFileFormatsType,
    console_level: LogLevel,
    console_format: FormatOption,
    colorize_console: bool,
    log_date_format: LogDateFormat,
    log_email_notifier_enable: bool,
    log_email_notifier_log_levels: NotifierLogLevels,
    log_email_notifier_log_format: FormatOption,
) -> None:
    """Sets up the logging configuration based on the provided parameters.

    This function initializes and configures logging for the application,
    including file-based logging, console output, and optional email notifications.
    It will skip configuration if automatic initialization is disabled.

    Args:
        log_levels (LogLevels): A list specifying the log levels for different handlers.
        log_dir (LogDir): The directory where log files will be stored.
        log_file_formats (LogFileFormatsType): The format of the log files.
        console_level (LogLevel): The log level for console output.
        console_format (FormatOption): The format for console log messages.
        colorize_console (bool): Whether to colorize console output.
        log_date_format (LogDateFormat): The date format used in log entries.
        log_email_notifier_enable (bool): If True, enables email notifications for logs.
        log_email_notifier_log_levels (NotifierLogLevels): The log levels for the email notifier.
        log_email_notifier_log_format (FormatOption): The format for log messages in emails.

    Raises:
        ValueError: If invalid log configuration parameters are provided.
        ImproperlyConfigured: If the configuration is not set up correctly.
        AttributeError: If an attribute-related error occurs during setup.


    Example:
        >>> set_config(
        ...     log_levels=['DEBUG', 'INFO'],
        ...     log_dir='/var/log/myapp/',
        ...     log_file_formats={'INFO': '%(levelname)s %(asctime)s %(message)s'},
        ...     console_level='DEBUG',
        ...     console_format='{message}',
        ...     colorize_console=True,
        ...     log_date_format='%Y-%m-%d %H:%M:%S',
        ...     log_email_notifier_enable=False,
        ...     log_email_notifier_log_levels=['ERROR'],
        ...     log_email_notifier_log_format='%(module)s %(message)s'
        ... )

    Notes:
        - The function performs system checks and logs warnings if configuration issues are detected.
        - It also logs the current logging setup upon successful initialization.

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
    except (ValueError, ImproperlyConfigured, AttributeError, FileNotFoundError):
        import logging

        colors = AnsiColors()

        logging.warning(
            "\n"
            "========================%sDJANGO LOGGING%s"
            "========================\n"
            "%s[CONFIGURATION ERROR]%s"
            " A configuration issue has been detected.\n"
            "System checks will be run to provide more detailed information.\n"
            "==============================================================\n",
            colors.RED_BACKGROUND,
            colors.RESET,
            colors.RED,
            colors.RESET,
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
