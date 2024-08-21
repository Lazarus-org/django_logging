import os

from django_logging.constants.settings_types import (
    LogFileFormatsType,
    LOG_DIR_TYPE,
    LOG_FILE_LEVELS_TYPE,
    LOG_CONSOLE_FORMAT_TYPE,
    LOG_CONSOLE_LEVEL_TYPE,
    LOG_CONSOLE_COLORIZE_TYPE,
    LOG_DATE_FORMAT_TYPE,
    INITIALIZATION_MESSAGE_ENABLE_TYPE,
    LogEmailNotifierType,
)

# Default directory for logs
DEFAULT_LOG_DIR: LOG_DIR_TYPE = os.path.join(os.getcwd(), "logs")

# Default LogLevels in File Handlers
DEFAULT_LOG_FILE_LEVELS: LOG_FILE_LEVELS_TYPE = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


# Default log date format
DEFAULT_LOG_DATE_FORMAT: LOG_DATE_FORMAT_TYPE = "%Y-%m-%d %H:%M:%S"

# Default Auto initialization flag
DEFAULT_AUTO_INITIALIZATION_ENABLE: INITIALIZATION_MESSAGE_ENABLE_TYPE = True

# Default initialization message flag
DEFAULT_INITIALIZATION_MESSAGE_ENABLE: INITIALIZATION_MESSAGE_ENABLE_TYPE = True

# Default log formats in log files for each LogLevel
DEFAULT_LOG_FILE_FORMATS: LogFileFormatsType = {
    "DEBUG": 1,
    "INFO": 1,
    "WARNING": 1,
    "ERROR": 1,
    "CRITICAL": 1,
}

# Default LogLevel for console output
DEFAULT_LOG_CONSOLE_LEVEL: LOG_CONSOLE_LEVEL_TYPE = "DEBUG"

# Default log format for console output
DEFAULT_LOG_CONSOLE_FORMAT: LOG_CONSOLE_FORMAT_TYPE = 1

# Default colorize logs flag for console output
DEFAULT_LOG_CONSOLE_COLORIZE: LOG_CONSOLE_COLORIZE_TYPE = True

# Default Log Email Notifier Configs
DEFAULT_LOG_EMAIL_NOTIFIER: LogEmailNotifierType = {
    "ENABLE": False,
    "NOTIFY_ERROR": False,
    "NOTIFY_CRITICAL": False,
    "LOG_FORMAT": 1,
    "USE_TEMPLATE": True,
}
