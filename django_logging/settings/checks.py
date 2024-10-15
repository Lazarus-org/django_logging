from typing import Any, Dict, List

from django.core.checks import Error, register

from django_logging.constants import ALLOWED_FILE_FORMAT_TYPES, DefaultLoggingSettings
from django_logging.settings import settings_manager
from django_logging.validators.config_validators import (
    validate_boolean_setting,
    validate_date_format,
    validate_directory,
    validate_email_notifier,
    validate_extra_log_files,
    validate_format_option,
    validate_integer_setting,
    validate_log_file_format_types,
    validate_log_levels,
)
from django_logging.validators.email_settings_validator import check_email_settings


# pylint: disable=too-many-locals
@register()
def check_logging_settings(app_configs: Dict[str, Any], **kwargs: Any) -> List[Error]:
    """Check and validate logging settings in the Django configuration.

    This function performs a comprehensive validation of various logging-related
    settings defined in the Django configuration. It ensures that the provided
    settings conform to the expected structure and values, and it returns a list
    of errors if any issues are found.

    Parameters:
    -----------
    app_configs : Dict[str, Any]
        A dictionary containing application configurations. This is typically
        passed by Django during checks and is not directly used in this function.

    kwargs : Any
        Additional keyword arguments that can be passed during the check. This is
        not directly used in this function but allows for flexibility in extending
        checks in the future.

    Returns:
    --------
    List[Error]
        A list of `Error` objects, each representing a validation issue with the
        logging settings. If no issues are found, the list will be empty.

    Validations:
    ------------
    - LOG_DIR: Validates the logging directory path.
    - LOG_FILE_LEVELS: Validates the log levels for file logging.
    - LOG_FILE_FORMATS: Validates the log formats for file logging, ensuring
      they are provided as a dictionary with valid log levels as keys.
    - LOG_CONSOLE_FORMAT: Validates the log format for console logging.
    - LOG_CONSOLE_LEVEL: Validates the log level for console logging.
    - LOG_CONSOLE_COLORIZE: Validates whether console log colorization is enabled.
    - LOG_DATE_FORMAT: Validates the date format used in logging.
    - AUTO_INITIALIZATION_ENABLE: Validates whether automatic initialization is enabled.
    - INITIALIZATION_MESSAGE_ENABLE: Validates whether the initialization message is enabled.
    - LOG_EMAIL_NOTIFIER: Validates the email notifier configuration and its
      settings, including format, enablement, and related email settings.

    Notes:
    ------
    This function utilizes validators from `django_logging.validators`
    to perform detailed checks on each setting. If email notifications are enabled,
    additional checks are performed on email settings to ensure proper configuration.

    """
    errors: List[Error] = []
    logging_defaults = DefaultLoggingSettings()

    # Validate LOG_DIR
    errors.extend(validate_directory(settings_manager.log_dir, "LOG_DIR"))

    # Validate LOG_FILE_LEVELS
    log_file_levels = settings_manager.log_levels
    errors.extend(
        validate_log_levels(
            log_file_levels, "LOG_FILE_LEVELS", logging_defaults.log_levels  # type: ignore
        )
    )

    # Validate LOG_FILE_FORMATS
    log_file_formats = settings_manager.log_file_formats
    if isinstance(log_file_formats, dict):
        for level, format_option in log_file_formats.items():
            if level not in logging_defaults.log_levels:
                errors.append(
                    Error(
                        f"Invalid log level '{level}' in LOG_FILE_FORMATS.",
                        hint=f"Valid log levels are: {logging_defaults.log_levels}.",
                        id="django_logging.E019_LOG_FILE_FORMATS",
                    )
                )
            else:
                setting_name = f"LOG_FILE_FORMATS['{level}']"
                errors.extend(validate_format_option(format_option, setting_name))
    else:
        errors.append(
            Error(
                "LOG_FILE_FORMATS is not a dictionary.",
                hint="Ensure LOG_FILE_FORMATS is a dictionary with log levels as keys.",
                id="django_logging.E020_LOG_FILE_FORMATS",
            )
        )

    # Validate LOG_FILE_FORMAT_TYPES
    errors.extend(
        validate_log_file_format_types(
            settings_manager.log_file_format_types,
            "LOG_FILE_FORMAT_TYPES",
            logging_defaults.log_levels,
            ALLOWED_FILE_FORMAT_TYPES + ["NORMAL"],
        )
    )

    # Validate EXTRA_LOG_FILES
    errors.extend(
        validate_extra_log_files(
            settings_manager.extra_log_files,
            "EXTRA_LOG_FILES",
            logging_defaults.log_levels,
        )
    )

    # Validate LOG_CONSOLE_FORMAT
    errors.extend(validate_format_option(settings_manager.console_format, "LOG_CONSOLE_FORMAT"))  # type: ignore

    # Validate LOG_CONSOLE_LEVEL
    errors.extend(
        validate_log_levels(
            [settings_manager.console_level], "LOG_CONSOLE_LEVEL", logging_defaults.log_levels  # type: ignore
        )
    )

    # Validate LOG_CONSOLE_COLORIZE
    errors.extend(
        validate_boolean_setting(settings_manager.colorize_console, "LOG_CONSOLE_COLORIZE")  # type: ignore
    )

    # Validate LOG_DATE_FORMAT
    errors.extend(validate_date_format(settings_manager.log_date_format, "LOG_DATE_FORMAT"))  # type: ignore

    # Validate INCLUDE_LOG_iBOARD
    errors.extend(
        validate_boolean_setting(
            settings_manager.include_log_iboard, "INCLUDE_LOG_iBOARD"
        )
    )

    # Validate AUTO_INITIALIZATION_ENABLE
    errors.extend(
        validate_boolean_setting(
            settings_manager.auto_initialization_enabled, "AUTO_INITIALIZATION_ENABLE"
        )
    )

    # Validate INITIALIZATION_MESSAGE_ENABLE
    errors.extend(
        validate_boolean_setting(
            settings_manager.initialization_message_enabled,
            "INITIALIZATION_MESSAGE_ENABLE",
        )
    )

    # Validate LOG_SQL_QUERIES_ENABLE
    errors.extend(
        validate_boolean_setting(
            settings_manager.log_sql_queries_enabled, "LOG_SQL_QUERIES_ENABLE"
        )
    )

    # Validate LOG_DIR_SIZE_LIMIT
    errors.extend(
        validate_integer_setting(
            settings_manager.log_dir_size_limit, "LOG_DIR_SIZE_LIMIT"
        )
    )

    # Validate LOG_EMAIL_NOTIFIER
    log_email_notifier = settings_manager.email_notifier
    errors.extend(validate_email_notifier(log_email_notifier))  # type: ignore

    if log_email_notifier.get("ENABLE", False):  # type: ignore
        errors.extend(check_email_settings())

    return errors
