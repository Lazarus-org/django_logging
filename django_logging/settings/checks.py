from typing import Any, Dict, List

from django.core.checks import Error, register

from django_logging.constants import DefaultLoggingSettings
from django_logging.utils.get_conf import (
    get_config,
    is_auto_initialization_enabled,
    is_initialization_message_enabled,
)
from django_logging.validators.config_validators import (
    validate_boolean_setting,
    validate_date_format,
    validate_directory,
    validate_email_notifier,
    validate_format_option,
    validate_log_levels,
)
from django_logging.validators.email_settings_validator import check_email_settings


@register()
def check_logging_settings(app_configs: Dict[str, Any], **kwargs: Any) -> List[Error]:
    errors: List[Error] = []

    log_settings = get_config(extra_info=True)
    logging_defaults = DefaultLoggingSettings()

    # Validate LOG_DIR
    errors.extend(validate_directory(log_settings.get("log_dir"), "LOG_DIR"))  # type: ignore

    # Validate LOG_FILE_LEVELS
    log_file_levels = log_settings.get("log_levels")
    errors.extend(
        validate_log_levels(
            log_file_levels, "LOG_FILE_LEVELS", logging_defaults.log_levels  # type: ignore
        )
    )

    # Validate LOG_FILE_FORMATS
    log_file_formats = log_settings.get(
        "log_file_formats", logging_defaults.log_file_formats
    )
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

    # Validate LOG_CONSOLE_FORMAT
    log_console_format = log_settings.get("console_format")
    errors.extend(validate_format_option(log_console_format, "LOG_CONSOLE_FORMAT"))  # type: ignore

    # Validate LOG_CONSOLE_LEVEL
    log_console_level = log_settings.get("console_level")
    errors.extend(
        validate_log_levels(
            [log_console_level], "LOG_CONSOLE_LEVEL", logging_defaults.log_levels  # type: ignore
        )
    )

    # Validate LOG_CONSOLE_COLORIZE
    log_console_colorize = log_settings.get("colorize_console")
    errors.extend(
        validate_boolean_setting(log_console_colorize, "LOG_CONSOLE_COLORIZE")  # type: ignore
    )

    # Validate LOG_DATE_FORMAT
    log_date_format = log_settings.get("log_date_format")
    errors.extend(validate_date_format(log_date_format, "LOG_DATE_FORMAT"))  # type: ignore

    # Validate AUTO_INITIALIZATION_ENABLE
    errors.extend(
        validate_boolean_setting(
            is_auto_initialization_enabled(), "AUTO_INITIALIZATION_ENABLE"
        )
    )

    # Validate INITIALIZATION_MESSAGE_ENABLE
    errors.extend(
        validate_boolean_setting(
            is_initialization_message_enabled(), "INITIALIZATION_MESSAGE_ENABLE"
        )
    )

    # Validate LOG_EMAIL_NOTIFIER
    log_email_notifier = log_settings.get("log_email_notifier")
    errors.extend(validate_email_notifier(log_email_notifier))  # type: ignore

    if log_email_notifier.get("ENABLE", False):  # type: ignore
        errors.extend(check_email_settings())

    return errors
