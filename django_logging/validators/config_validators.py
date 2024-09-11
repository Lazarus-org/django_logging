import os
import re
from typing import List

from django.core.checks import Error

from django_logging.constants import (
    FORMAT_OPTIONS,
    LOG_FORMAT_SPECIFIERS,
    VALID_DIRECTIVES,
)
from django_logging.constants.config_types import (
    FormatOption,
    LogEmailNotifierType,
    LogLevels,
)


def validate_directory(path: str, config_name: str) -> List[Error]:
    errors = []
    if not isinstance(path, str):
        errors.append(
            Error(
                f"{config_name} is not a string.",
                hint=f"Ensure {config_name} is a valid directory path string.",
                id=f"django_logging.E001_{config_name}",
            )
        )
    elif not os.path.exists(path):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception:  # pylint: disable=broad-exception-caught
            errors.append(
                Error(
                    f"The path specified in {config_name} is not a valid path.",
                    hint=f"Ensure the path set in {config_name} is valid.",
                    id=f"django_logging.E002_{config_name}",
                )
            )

    elif not os.path.isdir(path):
        errors.append(
            Error(
                f"The path specified in {config_name} is not a directory.",
                hint=f"Ensure {config_name} points to a valid directory.",
                id=f"django_logging.E003_{config_name}",
            )
        )
    return errors


def validate_log_levels(
    log_levels: LogLevels,
    config_name: str,
    valid_levels: LogLevels,
) -> List[Error]:
    errors = []
    if not isinstance(log_levels, list):
        errors.append(
            Error(
                f"{config_name} is not a list.",
                hint=f"Ensure {config_name} is a list of log level strings.",
                id=f"django_logging.E004_{config_name}",
            )
        )
    elif not log_levels:
        errors.append(
            Error(
                f"{config_name} is an empty list.",
                hint=f"Ensure {config_name} contains at least one log level.",
                id=f"django_logging.E005_{config_name}",
            )
        )
    else:
        for level in log_levels:
            if not isinstance(level, str):
                errors.append(
                    Error(
                        f"Invalid type in {config_name}: {level} is not a string.",
                        hint=f"Ensure all elements in {config_name} are strings.",
                        id=f"django_logging.E006_{config_name}",
                    )
                )
            elif level not in valid_levels:
                errors.append(
                    Error(
                        f"Invalid log level '{level}' in {config_name}.",
                        hint=f"Valid log levels are: {valid_levels}.",
                        id=f"django_logging.E007_{config_name}",
                    )
                )
    return errors


def validate_format_string(format_str: str, config_name: str) -> List[Error]:
    errors = []
    if not isinstance(format_str, str):
        errors.append(
            Error(
                f"{config_name} is not a string.",
                hint=f"Ensure {config_name} is a valid format string.",
                id=f"django_logging.E008_{config_name}",
            )
        )
    elif not format_str:
        errors.append(
            Error(
                f"{config_name} is an empty string.",
                hint=f"Ensure {config_name} is not empty.",
                id=f"django_logging.E009_{config_name}",
            )
        )
    else:
        format_specifiers = re.findall(r"%\((.*?)\)", format_str)
        if not format_specifiers:
            errors.append(
                Error(
                    f"{config_name} contains no format specifiers.",
                    hint=f"Include at least one valid format specifier in {config_name}.",
                    id=f"django_logging.E010_{config_name}",
                )
            )
        else:
            invalid_specifiers = [
                spec for spec in format_specifiers if spec not in LOG_FORMAT_SPECIFIERS
            ]
            if invalid_specifiers:
                errors.append(
                    Error(
                        f"{config_name} contains invalid format specifiers: {invalid_specifiers}.",
                        hint=f"Valid specifiers are: {LOG_FORMAT_SPECIFIERS}.",
                        id=f"django_logging.E011_{config_name}",
                    )
                )
    return errors


def validate_format_option(
    format_option: FormatOption, config_name: str
) -> List[Error]:
    errors = []
    if isinstance(format_option, int):
        if format_option not in FORMAT_OPTIONS:
            errors.append(
                Error(
                    f"Invalid format option '{format_option}' for {config_name}.",
                    hint=f"Valid format options are: {list(FORMAT_OPTIONS.keys())}.",
                    id=f"django_logging.E012_{config_name}",
                )
            )
    elif isinstance(format_option, str):
        errors.extend(validate_format_string(format_option, config_name))
    else:
        errors.append(
            Error(
                f"{config_name} has invalid type.",
                hint=f"{config_name} should be either an integer referencing FORMAT_OPTIONS or a format string.",
                id=f"django_logging.E013_{config_name}",
            )
        )
    return errors


def validate_boolean_setting(value: bool, config_name: str) -> List[Error]:
    errors: List[Error] = []
    if not isinstance(value, bool):
        errors.append(
            Error(
                f"{config_name} is not a boolean.",
                hint=f"Ensure {config_name} is either True or False.",
                id=f"django_logging.E014_{config_name}",
            )
        )
    return errors


def validate_date_format(date_format: str, config_name: str) -> List[Error]:
    def parse_format_string(format_string: str) -> set:
        """Extract format specifiers from the format string."""
        return set(re.findall(r"%[a-zA-Z]", format_string))

    errors = []
    if not isinstance(date_format, str):
        errors.append(
            Error(
                f"{config_name} is not a string.",
                hint=f"Ensure {config_name} is a valid date format string.",
                id=f"django_logging.E015_{config_name}",
            )
        )
    else:
        # Extract directives from the provided format string
        directives = parse_format_string(date_format)

        # Validate against allowed directives
        invalid_directives = directives - VALID_DIRECTIVES
        if invalid_directives:
            errors.append(
                Error(
                    f"{config_name} contains invalid format directives.",
                    hint=f"Invalid directives: {', '.join(invalid_directives)}."
                    f"\n Ensure {config_name} follows valid strftime directives.",
                    id=f"django_logging.E016_{config_name}",
                )
            )
    return errors


def validate_email_notifier(notifier_config: LogEmailNotifierType) -> List[Error]:
    errors = []
    if not isinstance(notifier_config, dict):
        errors.append(
            Error(
                "LOG_EMAIL_NOTIFIER is not a dictionary.",
                hint="Ensure LOG_EMAIL_NOTIFIER is a dictionary with appropriate configuration keys.",
                id="django_logging.E017_LOG_EMAIL_NOTIFIER",
            )
        )
        return errors

    for key, value in notifier_config.items():
        expected_type = type(value)
        config_name = f"LOG_EMAIL_NOTIFIER['{key}']"
        bool_attrs = ["ENABLE", "NOTIFY_ERROR", "NOTIFY_CRITICAL", "USE_TEMPLATE"]

        if expected_type is bool and key in bool_attrs:
            errors.extend(validate_boolean_setting(bool(value), config_name))
        elif isinstance(value, (int, str)) and key == "LOG_FORMAT":
            errors.extend(validate_format_option(value, config_name))

        else:
            errors.append(
                Error(
                    f"Unknown type '{expected_type}' for {config_name}.",
                    hint="Check the expected types in LogEmailNotifierType.",
                    id=f"django_logging.E018_{config_name}",
                )
            )
    return errors


def validate_integer_setting(value: int, config_name: str) -> List[Error]:
    errors: List[Error] = []
    if not isinstance(value, int) or value < 0:
        errors.append(
            Error(
                f"{config_name} is not a valid integer.",
                hint=f"Ensure {config_name} is a valid positive integer",
                id=f"django_logging.E019_{config_name}",
            )
        )
    return errors
