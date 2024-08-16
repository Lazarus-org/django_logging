import logging
import logging.config
import os
from typing import List, Dict, Optional


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
    ) -> None:
        self.log_levels = log_levels
        self.log_dir = log_dir


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
                "formatter": "default",
                "level": level,
            }
            for level, log_file in self.log_files.items()
        }
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": "DEBUG",
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
            "handlers": handlers,
            "loggers": loggers,
            "root": {"level": "DEBUG", "handlers": list(handlers.keys())},
            "disable_existing_loggers": False,
        }

        logging.config.dictConfig(config)
