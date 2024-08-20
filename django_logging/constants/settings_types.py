from typing import TypedDict, Union, List, Literal

FormatOption = Union[int, str]


class LogEmailNotifierType(TypedDict, total=False):
    ENABLE: bool
    NOTIFY_ERROR: bool
    NOTIFY_CRITICAL: bool
    LOG_FORMAT: FormatOption
    USE_TEMPLATE: bool


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogFileFormatsType(TypedDict, total=False):
    DEBUG: FormatOption
    INFO: FormatOption
    WARNING: FormatOption
    ERROR: FormatOption
    CRITICAL: FormatOption


# Type Aliases for other configurations
LOG_DIR_TYPE = str
LOG_FILE_LEVELS_TYPE = List[str]
LOG_DATE_FORMAT_TYPE = str
INITIALIZATION_MESSAGE_ENABLE_TYPE = bool
LOG_CONSOLE_LEVEL_TYPE = LogLevel
LOG_CONSOLE_FORMAT_TYPE = FormatOption
LOG_CONSOLE_COLORIZE_TYPE = bool
