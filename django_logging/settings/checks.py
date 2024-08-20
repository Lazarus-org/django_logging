from django.conf import settings
from django.core.checks import Error, register
from typing import Dict, Any, List

from django_logging.constants import (
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FILE_LEVELS,
    DEFAULT_LOG_DATE_FORMAT,
    DEFAULT_LOG_EMAIL_NOTIFIER,
    DEFAULT_LOG_CONSOLE_LEVEL,
    DEFAULT_LOG_CONSOLE_FORMAT,
    DEFAULT_LOG_CONSOLE_COLORIZE,
    DEFAULT_LOG_FILE_FORMATS,
    DEFAULT_INITIALIZATION_MESSAGE_ENABLE,
)

from django_logging.validators.config_validators import (
    validate_directory,
    validate_log_levels,
    validate_date_format,
    validate_format_option,
    validate_email_notifier,
    validate_boolean_setting,
)
from django_logging.validators.email_settings_validator import check_email_settings


@register()
def check_logging_settings(app_configs: Dict[str, Any], **kwargs: Any) -> List[Error]:
    errors: List[Error] = []

    log_settings = getattr(settings, "DJANGO_LOGGING", {})

    # Validate LOG_DIR
    log_dir = log_settings.get("LOG_DIR", DEFAULT_LOG_DIR)
    errors.extend(validate_directory(log_dir, "LOG_DIR"))

    # Validate LOG_FILE_LEVELS
    log_file_levels = log_settings.get("LOG_FILE_LEVELS", DEFAULT_LOG_FILE_LEVELS)
    errors.extend(
        validate_log_levels(log_file_levels, "LOG_FILE_LEVELS", DEFAULT_LOG_FILE_LEVELS)
    )

    # Validate LOG_FILE_FORMATS
    log_file_formats = log_settings.get("LOG_FILE_FORMATS", DEFAULT_LOG_FILE_FORMATS)
    if isinstance(log_file_formats, dict):
        for level, format_option in log_file_formats.items():
            if level not in DEFAULT_LOG_FILE_LEVELS:
                errors.append(
                    Error(
                        f"Invalid log level '{level}' in LOG_FILE_FORMATS.",
                        hint=f"Valid log levels are: {DEFAULT_LOG_FILE_LEVELS}.",
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
    log_console_format = log_settings.get(
        "LOG_CONSOLE_FORMAT", DEFAULT_LOG_CONSOLE_FORMAT
    )
    errors.extend(validate_format_option(log_console_format, "LOG_CONSOLE_FORMAT"))

    # Validate LOG_CONSOLE_LEVEL
    log_console_level = log_settings.get("LOG_CONSOLE_LEVEL", DEFAULT_LOG_CONSOLE_LEVEL)
    errors.extend(
        validate_log_levels(
            [log_console_level], "LOG_CONSOLE_LEVEL", DEFAULT_LOG_FILE_LEVELS
        )
    )

    # Validate LOG_CONSOLE_COLORIZE
    log_console_colorize = log_settings.get(
        "LOG_CONSOLE_COLORIZE", DEFAULT_LOG_CONSOLE_COLORIZE
    )
    errors.extend(
        validate_boolean_setting(log_console_colorize, "LOG_CONSOLE_COLORIZE")
    )

    # Validate LOG_DATE_FORMAT
    log_date_format = log_settings.get("LOG_DATE_FORMAT", DEFAULT_LOG_DATE_FORMAT)
    errors.extend(validate_date_format(log_date_format, "LOG_DATE_FORMAT"))

    # Validate INITIALIZATION_MESSAGE
    initialization_message = log_settings.get(
        "INITIALIZATION_MESSAGE_ENABLED", DEFAULT_INITIALIZATION_MESSAGE_ENABLE
    )
    errors.extend(
        validate_boolean_setting(initialization_message, "INITIALIZATION_MESSAGE")
    )

    # Validate LOG_EMAIL_NOTIFIER
    log_email_notifier = log_settings.get(
        "LOG_EMAIL_NOTIFIER", DEFAULT_LOG_EMAIL_NOTIFIER
    )
    errors.extend(validate_email_notifier(log_email_notifier))

    if log_email_notifier.get("ENABLE", False):
        errors.extend(check_email_settings())

    return errors