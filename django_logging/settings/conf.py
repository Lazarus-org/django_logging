import logging
import logging.config
import os
from typing import Dict, List, Optional

from django_logging.constants import (
    ALLOWED_EXTRA_FILE_TYPES,
    ALLOWED_FILE_FORMAT_TYPES,
    FORMAT_OPTIONS,
    DefaultLoggingSettings,
)
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
from django_logging.filters.log_level_filter import LoggingLevelFilter


# pylint: disable=too-many-instance-attributes, too-many-arguments, too-many-positional-arguments, too-many-locals
class LogConfig:
    """Configuration class for django_logging.

    Attributes:
        log_levels (List[str]): A list of log levels to be used in logging.
        log_dir (str): The directory where log files will be stored.
        log_rotation (LogRotationConfig): Global rotation defaults.
        log_rotation_overrides (LogRotationOverrides): Per-level rotation overrides.

    """

    def __init__(
        self,
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
        log_rotation: Optional[LogRotationConfig] = None,
        log_rotation_overrides: Optional[LogRotationOverrides] = None,
    ) -> None:
        self.log_levels = log_levels
        self.log_dir = log_dir
        self.log_file_formats = self._resolve_file_formats(log_file_formats)
        self.log_date_format = log_date_format
        self.console_level = console_level
        self.colorize_console = colorize_console
        self.console_format = self.resolve_format(
            console_format, use_colors=self.colorize_console
        )
        self.email_notifier_enable = log_email_notifier_enable
        self.email_notifier_log_levels = log_email_notifier_log_levels
        self.email_notifier_log_format = self.resolve_format(
            log_email_notifier_log_format
        )
        self.log_file_format_types = log_file_format_types
        self.extra_log_files = extra_log_files

        # Rotation — fall back to defaults when not supplied
        default_rotation = dict(DefaultLoggingSettings().log_rotation)
        if log_rotation:
            default_rotation.update(log_rotation)
        self.log_rotation: LogRotationConfig = default_rotation  # type: ignore[assignment]
        self.log_rotation_overrides: LogRotationOverrides = log_rotation_overrides or {}

    # ------------------------------------------------------------------
    # Format helpers
    # ------------------------------------------------------------------

    def _resolve_file_formats(self, log_file_formats: LogFileFormats) -> Dict:
        resolved_formats = {}
        for level in self.log_levels:
            format_option = log_file_formats.get(level, None)
            if format_option:
                if isinstance(format_option, int):
                    resolved_formats[level] = FORMAT_OPTIONS.get(
                        format_option, FORMAT_OPTIONS[1]
                    )
                else:
                    resolved_formats[level] = format_option
            else:
                resolved_formats[level] = FORMAT_OPTIONS[1]

            colored_format = resolved_formats[level]
            resolved_formats[level] = self.remove_ansi_escape_sequences(colored_format)

        return resolved_formats

    @staticmethod
    def remove_ansi_escape_sequences(log_message: str) -> str:
        """Remove ANSI escape sequences from log messages."""
        import re

        ansi_escape = re.compile(r"(?:\x1B[@-_][0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", log_message)

    @staticmethod
    def resolve_format(_format: FormatOption, use_colors: bool = False) -> str:
        resolved_format: str = ""
        if _format:
            if isinstance(_format, int):
                resolved_format = FORMAT_OPTIONS.get(_format, FORMAT_OPTIONS[1])
            elif isinstance(_format, str):
                resolved_format = _format

        else:
            resolved_format = FORMAT_OPTIONS[1]

        # If colors are not enabled, strip out color codes, if provided in formats
        if not use_colors:
            resolved_format = LogConfig.remove_ansi_escape_sequences(resolved_format)

        return resolved_format

    def get_rotation_config_for_level(self, level: str) -> LogRotationConfig:
        """Return the effective rotation config for *level*.

        Per-level overrides are shallow-merged on top of the global
        rotation defaults so callers only need to specify the keys that
        differ.

        """
        effective = dict(self.log_rotation)
        override = self.log_rotation_overrides.get(level, {})
        effective.update(override)
        return effective  # type: ignore[return-value]


class LogManager:
    """Manages the creation and configuration of log files.

    Attributes:
        log_config (LogConfig): The logging configuration.
        log_files (Dict[str, str]): A dictionary mapping log levels to file paths.

    """

    def __init__(self, log_config: LogConfig) -> None:
        self.log_config = log_config
        self.log_files: Dict[str, str] = {}

    def create_log_files(self) -> None:
        """Creates log files based on the log levels in the configuration."""
        for log_level in self.log_config.log_levels:
            fmt_type = self.log_config.log_file_format_types.get(log_level, "").lower()
            extra_file = self.log_config.extra_log_files.get(log_level, False)

            if extra_file and fmt_type.upper() in ALLOWED_EXTRA_FILE_TYPES:
                # Use separate files for extra file format structure
                log_file_path = os.path.join(
                    self.log_config.log_dir,
                    fmt_type,
                    f"{log_level.lower()}.{fmt_type}",
                )
            else:
                # Use regular log file for normal, JSON, or XML
                log_file_path = os.path.join(
                    self.log_config.log_dir, f"{log_level.lower()}.log"
                )

            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            if not os.path.exists(log_file_path):
                with open(log_file_path, "w", encoding="utf-8"):
                    pass
            self.log_files[log_level] = log_file_path

    def get_log_file(self, log_level: LogLevel) -> Optional[str]:
        """Retrieves the file path for a given log level.

        Args:
            log_level (str): The log level to retrieve the file for.

        Returns:
            Optional[str]: The file path associated with the log level, or None if not found.

        """
        return self.log_files.get(log_level)

    def _build_file_handler_config(self, log_file: str, level: str) -> Dict:
        """Return a dictConfig-compatible handler dict for *level*.

        The handler class and its kwargs are chosen based on the effective
        rotation config for the level:

        * ``TYPE = "none"``  → plain ``logging.FileHandler``
        * ``TYPE = "size"``  → ``RotatingFileHandler`` (or compressed variant)
        * ``TYPE = "time"``  → ``TimedRotatingFileHandler`` (or compressed variant)

        """
        rotation = self.log_config.get_rotation_config_for_level(level)
        rotation_type = str(rotation.get("TYPE", "none")).lower()
        compress = bool(rotation.get("COMPRESS", False))
        backup_count = int(rotation.get("BACKUP_COUNT", 5))

        if rotation_type == "size":
            max_bytes = int(rotation.get("MAX_BYTES", 10_485_760))
            if compress:
                handler_class = "django_logging.handlers.CompressedRotatingFileHandler"
            else:
                handler_class = "logging.handlers.RotatingFileHandler"
            return {
                "class": handler_class,
                "filename": log_file,
                "maxBytes": max_bytes,
                "backupCount": backup_count,
            }

        if rotation_type == "time":
            when = str(rotation.get("WHEN", "midnight"))
            interval = int(rotation.get("INTERVAL", 1))
            if compress:
                handler_class = (
                    "django_logging.handlers.CompressedTimedRotatingFileHandler"
                )
            else:
                handler_class = "logging.handlers.TimedRotatingFileHandler"
            return {
                "class": handler_class,
                "filename": log_file,
                "when": when,
                "interval": interval,
                "backupCount": backup_count,
            }

        # default: plain FileHandler
        return {
            "class": "logging.FileHandler",
            "filename": log_file,
        }

    def set_conf(self) -> None:
        """Sets the logging configuration using the generated log files."""
        formatters: Dict = {}
        default_settings = DefaultLoggingSettings()

        # Build file handlers — each level gets its own handler with the
        # appropriate rotation strategy.
        handlers: Dict = {}
        for level, log_file in self.log_files.items():
            handler_cfg = self._build_file_handler_config(log_file, level)
            handler_cfg.update(
                {
                    "formatter": level.lower(),
                    "level": level,
                    "filters": [level.lower(), "context_var_filter"],
                }
            )
            handlers[level.lower()] = handler_cfg

        # Console handler
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": self.log_config.console_level,
            "filters": ["context_var_filter"],
        }

        # Email handlers (optional)
        email_handler = {
            f"email_{level.lower()}": {
                "class": "django_logging.handlers.EmailHandler",
                "formatter": "email",
                "level": level,
                "filters": [level.lower(), "context_var_filter"],
            }
            for level in self.log_config.email_notifier_log_levels
            if level
        }
        if self.log_config.email_notifier_enable:
            handlers.update(email_handler)

        # Filters
        filters: Dict = {
            level.lower(): {
                "()": LoggingLevelFilter,
                "logging_level": getattr(logging, level),
            }
            for level in default_settings.log_levels
        }

        # ContextVarFilter for context variables
        filters["context_var_filter"] = {
            "()": "django_logging.filters.ContextVarFilter",
        }

        # Formatters
        for level in self.log_config.log_levels:
            formatter = {
                level.lower(): {
                    "format": self.log_config.log_file_formats[level],
                    "datefmt": self.log_config.log_date_format,
                }
            }
            fmt_type = self.log_config.log_file_format_types.get(level, "None").upper()
            if fmt_type in ALLOWED_FILE_FORMAT_TYPES:
                formatter[level.lower()].update(
                    {"()": f"django_logging.formatters.{fmt_type}Formatter"}
                )
            formatters.update(formatter)

        formatters["console"] = {
            "format": self.log_config.console_format,
            "datefmt": self.log_config.log_date_format,
        }
        if self.log_config.colorize_console:
            formatters["console"].update(
                {"()": "django_logging.formatters.ColoredFormatter"}
            )

        formatters["email"] = {
            "format": self.log_config.email_notifier_log_format,
            "datefmt": self.log_config.log_date_format,
        }

        loggers: Dict = {
            level.lower(): {
                "level": level,
                "handlers": [level.lower()],
                "propagate": False,
            }
            for level in self.log_config.log_levels
        }

        config = {
            "version": 1,
            "formatters": formatters,
            "handlers": handlers,
            "filters": filters,
            "loggers": loggers,
            "root": {"level": "DEBUG", "handlers": list(handlers.keys())},
            "disable_existing_loggers": False,
        }

        logging.config.dictConfig(config)
