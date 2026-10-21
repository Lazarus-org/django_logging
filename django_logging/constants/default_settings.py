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
    LogRotationConfig,
    LogRotationOverrides,
)
from django_logging.constants.request_logging import REQUEST_LOGGING_DEFAULTS
from django_logging.constants.structured_logging import STRUCTURED_LOGGING_DEFAULTS


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
    logging_setup_mode: str = "additive"
    initialization_message_enable: bool = True
    log_sql_queries_enable: bool = False
    log_size_audit_in_request: bool = False
    request_logging: dict = field(
        default_factory=lambda: dict(REQUEST_LOGGING_DEFAULTS)
    )
    structured_logging: dict = field(
        default_factory=lambda: dict(STRUCTURED_LOGGING_DEFAULTS)
    )
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
                "MAX_CONCURRENT": 4,
                "SMTP_TIMEOUT": 10,
            },
        )
    )

    # --- Rotation defaults ---
    # Applied to all levels unless LOG_ROTATION_OVERRIDES provides per-level values.
    log_rotation: LogRotationConfig = field(
        default_factory=lambda: cast(
            LogRotationConfig,
            {
                "TYPE": "none",  # no rotation by default (plain FileHandler)
                "MAX_BYTES": 10_485_760,  # 10 MB — used when TYPE="size"
                "BACKUP_COUNT": 5,  # rotated files to keep
                "WHEN": "midnight",  # used when TYPE="time"
                "INTERVAL": 1,
                "COMPRESS": False,  # gzip old files on rotate
            },
        )
    )
    log_rotation_overrides: LogRotationOverrides = field(
        default_factory=lambda: cast(LogRotationOverrides, {})
    )


@dataclass
class DefaultConsoleSettings:
    log_console_level: LogLevel = "DEBUG"
    log_console_format: FormatOption = 1
    log_console_colorize: bool = True
