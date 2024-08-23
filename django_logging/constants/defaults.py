import os
from dataclasses import dataclass, field

from django_logging.constants.settings_types import (
    LogFileFormatsType,
    LogDir,
    LogLevel,
    LogLevels,
    FormatOption,
    LogDateFormat,
    LogEmailNotifierType,
)


@dataclass(frozen=True)
class DefaultLoggingSettings:
    log_dir: LogDir = field(default_factory=lambda: os.path.join(os.getcwd(), "logs"))
    log_levels: LogLevels = field(
        default_factory=lambda: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    log_date_format: LogDateFormat = "%Y-%m-%d %H:%M:%S"
    auto_initialization_enable: bool = True
    initialization_message_enable: bool = True
    log_file_formats: LogFileFormatsType = field(
        default_factory=lambda: {
            "DEBUG": 1,
            "INFO": 1,
            "WARNING": 1,
            "ERROR": 1,
            "CRITICAL": 1,
        }
    )
    log_console_level: LogLevel = "DEBUG"
    log_console_format: FormatOption = 1
    log_console_colorize: bool = True
    log_email_notifier: LogEmailNotifierType = field(
        default_factory=lambda: {
            "ENABLE": False,
            "NOTIFY_ERROR": False,
            "NOTIFY_CRITICAL": False,
            "LOG_FORMAT": 1,
            "USE_TEMPLATE": True,
        }
    )
