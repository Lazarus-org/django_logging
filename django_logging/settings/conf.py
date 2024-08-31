import logging
import logging.config
import os
from typing import Dict, List, Optional

from django_logging.constants import FORMAT_OPTIONS, DefaultLoggingSettings
from django_logging.constants.config_types import (
    FormatOption,
    LogDateFormat,
    LogDir,
    LogFileFormatsType,
    LogLevel,
    LogLevels,
    NotifierLogLevels,
)
from django_logging.filters.log_level_filter import LoggingLevelFilter


# pylint: disable=too-many-instance-attributes, too-many-arguments
class LogConfig:
    """Configuration class for django_logging.

    Attributes:
        log_levels (List[str]): A list of log levels to be used in logging.
        log_dir (str): The directory where log files will be stored.

    """

    def __init__(
        self,
        log_levels: LogLevels,
        log_dir: LogDir,
        log_file_formats: LogFileFormatsType,
        console_level: LogLevel,
        console_format: FormatOption,
        colorize_console: bool,
        log_date_format: LogDateFormat,
        log_email_notifier_enable: bool,
        log_email_notifier_log_levels: NotifierLogLevels,
        log_email_notifier_log_format: FormatOption,
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

    def _resolve_file_formats(self, log_file_formats: LogFileFormatsType) -> Dict:
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

    def set_conf(self) -> None:
        """Sets the logging configuration using the generated log files."""
        default_settings = DefaultLoggingSettings()
        handlers = {
            level.lower(): {
                "class": "logging.FileHandler",
                "filename": log_file,
                "formatter": f"{level.lower()}",
                "level": level,
                "filters": [level.lower()],
            }
            for level, log_file in self.log_files.items()
        }
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": self.log_config.console_level,
        }
        email_handler = {
            f"email_{level.lower()}": {
                "class": "django_logging.handlers.EmailHandler",
                "formatter": "email",
                "level": level,
                "filters": [level.lower()],
            }
            for level in self.log_config.email_notifier_log_levels
            if level
        }
        if self.log_config.email_notifier_enable:
            handlers.update(email_handler)

        filters = {
            level.lower(): {
                "()": LoggingLevelFilter,
                "logging_level": getattr(logging, level),
            }
            for level in default_settings.log_levels
        }

        formatters = {
            level.lower(): {
                "format": self.log_config.log_file_formats[level],
                "datefmt": self.log_config.log_date_format,
            }
            for level in self.log_config.log_levels
        }
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

        loggers = {
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
