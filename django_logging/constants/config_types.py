from typing import List, Literal, TypedDict, Union

VALID_ROTATION_TYPES = {"none", "size", "time"}
VALID_TIMED_WHEN = {
    "s",
    "m",
    "h",
    "d",
    "midnight",
    "w0",
    "w1",
    "w2",
    "w3",
    "w4",
    "w5",
    "w6",
}

FormatOption = Union[int, str]

# Type Aliases for configurations
LogFileFormatType = Literal["JSON", "XML", "FLAT", "NORMAL"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogRotationType = Literal["none", "size", "time"]
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


class LogRotationConfig(TypedDict, total=False):
    """Top-level rotation defaults applied to all levels unless overridden."""

    TYPE: LogRotationType  # "none" | "size" | "time"
    MAX_BYTES: int  # used when TYPE="size"
    BACKUP_COUNT: int  # number of rotated files to keep
    WHEN: str  # used when TYPE="time" e.g. "midnight", "h", "W0"
    INTERVAL: int  # used when TYPE="time", default 1
    COMPRESS: bool  # gzip rotated files


class LogRotationOverrides(TypedDict, total=False):
    """Per-level overrides; each value is a partial LogRotationConfig."""

    DEBUG: LogRotationConfig
    INFO: LogRotationConfig
    WARNING: LogRotationConfig
    ERROR: LogRotationConfig
    CRITICAL: LogRotationConfig
