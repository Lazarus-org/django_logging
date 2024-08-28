from typing import List, Literal, TypedDict, Union

FormatOption = Union[int, str]


class LogEmailNotifierType(TypedDict, total=False):
    ENABLE: bool
    NOTIFY_ERROR: bool
    NOTIFY_CRITICAL: bool
    LOG_FORMAT: FormatOption
    USE_TEMPLATE: bool


class LogFileFormatsType(TypedDict, total=False):
    DEBUG: FormatOption
    INFO: FormatOption
    WARNING: FormatOption
    ERROR: FormatOption
    CRITICAL: FormatOption


# Type Aliases for other configurations
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogDir = str
LogLevels = List[LogLevel]
NotifierLogLevels = List[Literal["ERROR", "CRITICAL"]]
LogDateFormat = str
