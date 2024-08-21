import os
from dataclasses import dataclass, field

from django_logging.constants.settings_types import (
    LogFileFormatsType,
    LOG_DIR_TYPE,
    LOG_LEVELS_TYPE,
    LOG_CONSOLE_FORMAT_TYPE,
    LOG_CONSOLE_LEVEL_TYPE,
    LOG_CONSOLE_COLORIZE_TYPE,
    LOG_DATE_FORMAT_TYPE,
    INITIALIZATION_MESSAGE_ENABLE_TYPE,
    LogEmailNotifierType,
)


@dataclass(frozen=True)
class DefaultLoggingSettings:
    log_dir: LOG_DIR_TYPE = field(
        default_factory=lambda: os.path.join(os.getcwd(), "logs")
    )
    log_levels: LOG_LEVELS_TYPE = field(
        default_factory=lambda: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    log_date_format: LOG_DATE_FORMAT_TYPE = "%Y-%m-%d %H:%M:%S"
    auto_initialization_enable: INITIALIZATION_MESSAGE_ENABLE_TYPE = True
    initialization_message_enable: INITIALIZATION_MESSAGE_ENABLE_TYPE = True
    log_file_formats: LogFileFormatsType = field(
        default_factory=lambda: {
            "DEBUG": 1,
            "INFO": 1,
            "WARNING": 1,
            "ERROR": 1,
            "CRITICAL": 1,
        }
    )
    log_console_level: LOG_CONSOLE_LEVEL_TYPE = "DEBUG"
    log_console_format: LOG_CONSOLE_FORMAT_TYPE = 1
    log_console_colorize: LOG_CONSOLE_COLORIZE_TYPE = True
    log_email_notifier: LogEmailNotifierType = field(
        default_factory=lambda: {
            "ENABLE": False,
            "NOTIFY_ERROR": False,
            "NOTIFY_CRITICAL": False,
            "LOG_FORMAT": 1,
            "USE_TEMPLATE": True,
        }
    )
