import os
from typing import Any, Dict, List, Union

from django.conf import settings

from django_logging.constants import DefaultConsoleSettings, DefaultLoggingSettings
from django_logging.constants.config_types import (
    ExtraLogFiles,
    FormatOption,
    LogDateFormat,
    LogDir,
    LogEmailNotifier,
    LogFileFormats,
    LogFileFormatTypes,
    LogLevels,
    NotifierLogLevels,
)


# pylint: disable=too-many-instance-attributes
class SettingsManager:
    """Manages DJANGO_LOGGING settings for the Django Logging application. All
    configurations are initialized at once and accessible via attributes.

    Attributes:
        log_dir (str): The directory where log files are stored.
        log_levels (List[str]): List of logging levels (e.g., DEBUG, INFO).
        log_file_formats (Dict[str, Union[int, str]]): Log file formats, which can be integers or strings.
        log_file_format_types (Dict[str, str]): Format types (e.g., 'json', 'xml', 'flat', 'normal') for each logging level.
        extra_log_files (Dict[str, bool]): Boolean values indicating whether separate files (JSON, XML) should be used for each logging level.
        console_level (str): The logging level for console output.
        console_format (Union[int, str]): The format for console logs, either an integer or a string.
        colorize_console (bool): Whether to colorize console logs.
        log_date_format (str): The format used for timestamps in logs.
        email_notifier (Dict[str, Any]): Configuration for email notifications.
        email_notifier_enabled (bool): Whether email notifications are enabled.
        email_notifier_log_levels (List[str]): Levels that trigger email notifications.
        email_notifier_log_format (Union[int, str]): Log format used in email notifications, either an integer or a format string.
        auto_initialization_enabled (bool): Whether auto initialization of logging is enabled.
        initialization_message_enabled (bool): Whether to display an initialization message for logging.
        log_sql_queries_enabled (bool): Whether to log SQL queries in each request.
        log_dir_size_limit (int): The maximum size (in MB) allowed for the log directory.
        include_log_iboard (bool): Whether the Logiboard feature is included.
        use_email_notifier_template (bool): Whether to use a template for email notifications.

    """

    def __init__(self) -> None:
        """Initializes all settings from the Django settings, falling back to
        default values defined in DefaultLoggingSettings and
        DefaultConsoleSettings."""
        self.log_settings = getattr(settings, "DJANGO_LOGGING", {})
        if not isinstance(self.log_settings, dict):
            raise ValueError("DJANGO_LOGGING must be a dictionary with configs as keys")

        self.default_logging = DefaultLoggingSettings()
        self.default_console = DefaultConsoleSettings()

        # Initialize all configuration settings
        self.log_dir: LogDir = self.get(
            "LOG_DIR", os.path.join(os.getcwd(), self.default_logging.log_dir)
        )
        self.log_levels: LogLevels = self.get(
            "LOG_FILE_LEVELS", self.default_logging.log_levels
        )
        self.log_file_formats: LogFileFormats = self.get(
            "LOG_FILE_FORMATS", self.default_logging.log_file_formats
        )
        self.log_file_format_types: LogFileFormatTypes = self.get(
            "LOG_FILE_FORMAT_TYPES", self.default_logging.log_file_format_types
        )
        self.extra_log_files: ExtraLogFiles = self.get(
            "EXTRA_LOG_FILES", self.default_logging.extra_log_files
        )
        self.console_level: str = self.get(
            "LOG_CONSOLE_LEVEL", self.default_console.log_console_level
        )
        self.console_format: FormatOption = self.get(
            "LOG_CONSOLE_FORMAT", self.default_console.log_console_format
        )
        self.colorize_console: bool = self.get(
            "LOG_CONSOLE_COLORIZE", self.default_console.log_console_colorize
        )
        self.log_date_format: LogDateFormat = self.get(
            "LOG_DATE_FORMAT", self.default_logging.log_date_format
        )
        self.email_notifier: LogEmailNotifier = self.get(
            "LOG_EMAIL_NOTIFIER", self.default_logging.log_email_notifier
        )
        self.email_notifier_enabled: bool = self.email_notifier.get("ENABLE", False)
        self.email_notifier_log_levels: NotifierLogLevels = [
            "ERROR" if self.email_notifier.get("NOTIFY_ERROR", False) else None,
            ("CRITICAL" if self.email_notifier.get("NOTIFY_CRITICAL", False) else None),
        ]
        self.email_notifier_log_format: FormatOption = self.email_notifier.get(
            "LOG_FORMAT", 1
        )
        self.auto_initialization_enabled: bool = self.get(
            "AUTO_INITIALIZATION_ENABLE",
            self.default_logging.auto_initialization_enable,
        )
        self.initialization_message_enabled: bool = self.get(
            "INITIALIZATION_MESSAGE_ENABLE",
            self.default_logging.initialization_message_enable,
        )
        self.log_sql_queries_enabled: bool = self.get(
            "LOG_SQL_QUERIES_ENABLE", self.default_logging.log_sql_queries_enable
        )
        self.log_dir_size_limit: int = self.get(
            "LOG_DIR_SIZE_LIMIT", self.default_logging.log_dir_size_limit
        )
        self.include_log_iboard: bool = self.get(
            "INCLUDE_LOG_iBOARD", self.default_logging.include_log_iboard
        )
        self.use_email_notifier_template: bool = self.email_notifier.get(
            "USE_TEMPLATE", True
        )

    def get(self, key: str, default_value: Any) -> Any:
        """Retrieves a logging-related setting from the Django settings. If the
        setting is not present, returns the provided default value.

        Args:
            key (str): The key to look up in the logging settings.
            default_value (Any): The default value to return if the key is not found.

        Returns:
            Any: The value of the setting or the default value.

        """
        return self.log_settings.get(key, default_value)


settings_manager: SettingsManager = SettingsManager()
