from typing import List, Literal, TypedDict, Union

FormatOption = Union[int, str]

# Type Aliases for configurations
LogFileFormatType = Literal["JSON", "XML", "FLAT", "NORMAL"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogDir = str
LogLevels = List[LogLevel]
NotifierLogLevels = List[Union[Literal["ERROR", "CRITICAL"], None]]
LogDateFormat = str


class LogEmailNotifier(TypedDict, total=False):
    ENABLE: bool
    NOTIFY_ERROR: bool
    NOTIFY_CRITICAL: bool
    LOG_FORMAT: FormatOption
    USE_TEMPLATE: bool


class LogFileFormats(TypedDict, total=False):
    DEBUG: FormatOption
    INFO: FormatOption
    WARNING: FormatOption
    ERROR: FormatOption
    CRITICAL: FormatOption


class LogFileFormatTypes(TypedDict, total=False):
    DEBUG: LogFileFormatType
    INFO: LogFileFormatType
    WARNING: LogFileFormatType
    ERROR: LogFileFormatType
    CRITICAL: LogFileFormatType


class ExtraLogFiles(TypedDict, total=False):
    DEBUG: bool
    INFO: bool
    WARNING: bool
    ERROR: bool
    CRITICAL: bool
