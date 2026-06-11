import os

from django.core.exceptions import ImproperlyConfigured

from django_logging.constants.ansi_colors import AnsiColors
from django_logging.constants.config_types import (
    ExtraLogFiles,
    FormatOption,
    LogDateFormat,
    LogDir,
    LogFileFormats,
    LogFileFormatTypes,
    LogLevel,
    LogLevels,
    LogRotationConfig,
    LogRotationOverrides,
    NotifierLogLevels,
)
from django_logging.settings.conf import LogConfig, LogManager
from django_logging.utils.get_conf import (
    is_auto_initialization_enabled,
    is_initialization_message_enabled,
)


# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals
def set_config(
    log_levels: LogLevels,
    log_dir: LogDir,
    log_file_formats: LogFileFormats,
    log_file_format_types: LogFileFormatTypes,
    extra_log_files: ExtraLogFiles,
    console_level: LogLevel,
    console_format: FormatOption,
    colorize_console: bool,
    log_date_format: LogDateFormat,
    log_email_notifier_enable: bool,
    log_email_notifier_log_levels: NotifierLogLevels,
    log_email_notifier_log_format: FormatOption,
    log_rotation: LogRotationConfig = None,
    log_rotation_overrides: LogRotationOverrides = None,
) -> None:
    """Sets up the logging configuration based on the provided parameters.

    This function initializes and configures logging for the application,
    including file-based logging, console output, and optional email notifications.
    It will skip configuration if automatic initialization is disabled.

    Args:
        log_levels (LogLevels): A list specifying the log levels for different handlers.
        log_dir (LogDir): The directory where log files will be stored.
        log_file_formats (LogFileFormats): The format of the log files.
        log_file_format_types (LogFileFormatTypes): The format type per level.
        extra_log_files (ExtraLogFiles): Whether to create separate typed files per level.
        console_level (LogLevel): The log level for console output.
        console_format (FormatOption): The format for console log messages.
        colorize_console (bool): Whether to colorize console output.
        log_date_format (LogDateFormat): The date format used in log entries.
        log_email_notifier_enable (bool): If True, enables email notifications.
        log_email_notifier_log_levels (NotifierLogLevels): Levels that trigger email.
        log_email_notifier_log_format (FormatOption): Email log message format.
        log_rotation (LogRotationConfig): Global rotation defaults.
        log_rotation_overrides (LogRotationOverrides): Per-level rotation overrides.

    Raises:
        ValueError: If invalid log configuration parameters are provided.
        ImproperlyConfigured: If the configuration is not set up correctly.
        AttributeError: If an attribute-related error occurs during setup.

    """
    if not is_auto_initialization_enabled():
        return

    try:
        log_config = LogConfig(
            log_levels,
            log_dir,
            log_file_formats,
            log_file_format_types,
            extra_log_files,
            console_level,
            console_format,
            colorize_console,
            log_date_format,
            log_email_notifier_enable,
            log_email_notifier_log_levels,
            log_email_notifier_log_format,
            log_rotation=log_rotation,
            log_rotation_overrides=log_rotation_overrides,
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
            rotation_type = (log_rotation or {}).get("TYPE", "none")
            logger.info(
                "Logging initialized with the following configurations:"
                "\n\tLog File levels: %s."
                "\n\tLog files are being written to: %s."
                "\n\tConsole output level: %s."
                "\n\tColorize console: %s."
                "\n\tLog date format: %s."
                "\n\tEmail notifier enabled: %s."
                "\n\tLog rotation type: %s.",
                log_levels,
                log_dir,
                console_level or "default (DEBUG)",
                colorize_console,
                log_date_format,
                log_email_notifier_enable,
                rotation_type,
            )
