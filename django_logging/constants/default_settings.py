import os
from dataclasses import dataclass, field
from typing import cast

from django_logging.constants.config_types import (
    ExtraLogFiles,
    FormatOption,
    LogDateFormat,
    LogDir,
    LogEmailNotifier,
    LogFileFormats,
    LogFileFormatTypes,
    LogLevel,
    LogLevels,
)


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class DefaultLoggingSettings:
    log_dir: LogDir = field(default_factory=lambda: os.path.join(os.getcwd(), "logs"))
    log_dir_size_limit: int = 1024  # MB
    log_levels: LogLevels = field(
        default_factory=lambda: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    log_date_format: LogDateFormat = "%Y-%m-%d %H:%M:%S"
    auto_initialization_enable: bool = True
    initialization_message_enable: bool = True
    log_sql_queries_enable: bool = False
    include_log_iboard: bool = False
    log_file_formats: LogFileFormats = field(
        default_factory=lambda: cast(
            LogFileFormats,
            {
                "DEBUG": 1,
                "INFO": 1,
                "WARNING": 1,
                "ERROR": 1,
                "CRITICAL": 1,
            },
        )
    )
    log_file_format_types: LogFileFormatTypes = field(
        default_factory=lambda: cast(
            LogFileFormatTypes,
            {
                "DEBUG": "normal",
                "INFO": "normal",
                "WARNING": "normal",
                "ERROR": "normal",
                "CRITICAL": "normal",
            },
        )
    )

    extra_log_files: ExtraLogFiles = field(
        default_factory=lambda: cast(
            ExtraLogFiles,
            {
                "DEBUG": False,
                "INFO": False,
                "WARNING": False,
                "ERROR": False,
                "CRITICAL": False,
            },
        )
    )

    log_email_notifier: LogEmailNotifier = field(
        default_factory=lambda: cast(
            LogEmailNotifier,
            {
                "ENABLE": False,
                "NOTIFY_ERROR": False,
                "NOTIFY_CRITICAL": False,
                "LOG_FORMAT": 1,
                "USE_TEMPLATE": True,
            },
        )
    )


@dataclass
class DefaultConsoleSettings:
    log_console_level: LogLevel = "DEBUG"
    log_console_format: FormatOption = 1
    log_console_colorize: bool = True
