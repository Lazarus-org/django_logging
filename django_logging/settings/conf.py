import logging
import logging.config
import os
from typing import List, Dict, Optional, Union

from django_logging.constants import FORMAT_OPTIONS
from django_logging.filters.level_filter import LoggingLevelFilter


class LogConfig:
    """
    Configuration class for django_logging.

    Attributes:
        log_levels (List[str]): A list of log levels to be used in logging.
        log_dir (str): The directory where log files will be stored.
    """

    def __init__(
            self,
            log_levels: List[str],
            log_dir: str,
            log_file_formats: Dict[str, Union[int, str]],
            console_level: str,
            console_format: Optional[Union[int, str]],
            log_date_format: str,
            log_email_notifier_enable: bool,
            log_email_notifier_log_levels: List[str],
            log_email_notifier_log_format: Union[int, str],
    ) -> None:

        self.log_levels = log_levels
        self.log_dir = log_dir
        self.log_file_formats = self._resolve_file_formats(log_file_formats)
        self.log_date_format = log_date_format
        self.console_level = console_level
        self.console_format = self.resolve_format(console_format)
        self.email_notifier_enable = log_email_notifier_enable
        self.email_notifier_log_levels = log_email_notifier_log_levels
        self.email_notifier_log_format = self.resolve_format(
            log_email_notifier_log_format
        )

    def _resolve_file_formats(self, log_file_formats: Dict[str, Union[int, str]]) -> Dict:
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

        return resolved_formats

    @staticmethod
    def resolve_format(_format: Union[int, str]) -> str:
        if _format:
            if isinstance(_format, int):
                resolved_format = FORMAT_OPTIONS.get(_format, FORMAT_OPTIONS[1])
            else:
                resolved_format = _format
        else:
            resolved_format = FORMAT_OPTIONS[1]

        return resolved_format


class LogManager:
    """
    Manages the creation and configuration of log files.

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
                open(log_file_path, "w").close()
            self.log_files[log_level] = log_file_path

    def get_log_file(self, log_level: str) -> Optional[str]:
        """
        Retrieves the file path for a given log level.

        Args:
            log_level (str): The log level to retrieve the file for.

        Returns:
            Optional[str]: The file path associated with the log level, or None if not found.
        """
        return self.log_files.get(log_level)

    def set_conf(self) -> None:
        """Sets the logging configuration using the generated log files."""
        handlers = {
            level.lower(): {
                "class": "logging.FileHandler",
                "filename": log_file,
                "formatter": f"{level.lower()}",
                "level": level,
                "filters": [level.lower()]
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
            for level in self.log_config.log_levels
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
