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

    # Validate the mode even when auto-configuration is disabled so typos
    # cannot silently activate the wrong logging policy later.
    from django_logging.settings.manager import SettingsManager

    if SettingsManager().logging_setup_mode not in (
        "additive",
        "isolated",
        "replace_root",
    ):
        errors.append(
            Error(
                "LOGGING_SETUP_MODE must be 'additive', 'isolated', or 'replace_root'.",
                id="django_logging.E041_LOGGING_SETUP_MODE",
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

    # Legacy synchronous audits must be an explicit request-time opt-in.
    if not isinstance(SettingsManager().log_size_audit_in_request, bool):
        errors.append(
            Error(
                "LOG_SIZE_AUDIT_IN_REQUEST must be a boolean.",
                id="django_logging.E044_LOG_SIZE_AUDIT",
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


@register()
def check_rotation_settings(app_configs: Dict[str, Any], **kwargs: Any) -> List[Error]:
    """Validate LOG_ROTATION and LOG_ROTATION_OVERRIDES settings."""
    from django_logging.validators.config_validators import (
        validate_rotation_config,
        validate_rotation_overrides,
    )

    errors: List[Error] = []
    logging_defaults = DefaultLoggingSettings()

    # Validate LOG_ROTATION
    errors.extend(
        validate_rotation_config(
            settings_manager.log_rotation,
            "LOG_ROTATION",
            logging_defaults.log_levels,
        )
    )

    # Validate LOG_ROTATION_OVERRIDES
    errors.extend(
        validate_rotation_overrides(
            settings_manager.log_rotation_overrides,
            "LOG_ROTATION_OVERRIDES",
            logging_defaults.log_levels,
        )
    )

    # Validate effective per-level settings too: an override can inherit an
    # incompatible COMPRESS=True from global rotation defaults.
    if isinstance(settings_manager.log_rotation_overrides, dict) and isinstance(
        settings_manager.log_rotation, dict
    ):
        for level, override in settings_manager.log_rotation_overrides.items():
            if isinstance(override, dict):
                effective = {**settings_manager.log_rotation, **override}
                if (
                    str(effective.get("TYPE", "none")).lower() == "external"
                    and effective.get("COMPRESS") is True
                ):
                    if not (
                        str(settings_manager.log_rotation.get("TYPE", "none")).lower()
                        == "external"
                        and settings_manager.log_rotation.get("COMPRESS") is True
                        and "COMPRESS" not in override
                    ):
                        errors.append(
                            Error(
                                f"Effective rotation for {level} cannot combine TYPE='external' with COMPRESS=True.",
                                id="django_logging.E045_LOG_ROTATION_EFFECTIVE",
                            )
                        )

    return errors


@register()
def check_request_logging_settings(app_configs: Any, **kwargs: Any) -> List[Error]:
    """Validate the request logging subsection against its shared schema."""
    from django_logging.settings.manager import SettingsManager
    from django_logging.settings.request_logging import request_logging_errors

    # Read current Django settings instead of a potentially stale module-level
    # singleton (important for override_settings and Django's system checks).
    current = SettingsManager().request_logging
    return [
        Error(message, id="django_logging.E040_REQUEST_LOGGING")
        for message in request_logging_errors(current)
    ]


@register()
def check_structured_logging_settings(app_configs: Any, **kwargs: Any) -> List[Error]:
    """Check structured formatter options against the runtime schema."""
    from django_logging.settings.manager import SettingsManager
    from django_logging.settings.structured_logging import structured_logging_errors

    return [
        Error(message, id="django_logging.E042_STRUCTURED_LOGGING")
        for message in structured_logging_errors(SettingsManager().structured_logging)
    ]


@register()
def check_logging_components(app_configs: Any, **kwargs: Any) -> List[Error]:
    """Validate user component schema and references during Django checks."""
    from django_logging.settings.components import ComponentConfigurationError
    from django_logging.settings.conf import LogConfig, LogManager
    from django_logging.settings.manager import SettingsManager
    from django_logging.utils.get_conf import get_config

    try:
        options = get_config()
        # Read current configuration rather than a stale settings singleton
        # for Django override_settings/system-check invocations.
        current = SettingsManager()
        options.update(
            {
                "log_levels": current.log_levels,
                "log_dir": current.log_dir,
                "log_file_formats": current.log_file_formats,
                "log_file_format_types": current.log_file_format_types,
                "extra_log_files": current.extra_log_files,
                "console_level": current.console_level,
                "console_format": current.console_format,
                "colorize_console": current.colorize_console,
                "log_date_format": current.log_date_format,
                "log_email_notifier_enable": current.email_notifier_enabled,
                "log_email_notifier_log_levels": current.email_notifier_log_levels,
                "log_email_notifier_log_format": current.email_notifier_log_format,
                "log_rotation": current.log_rotation,
                "log_rotation_overrides": current.log_rotation_overrides,
                "structured_logging": current.structured_logging,
                "components": current.components,
            }
        )
        LogManager(LogConfig(**options)).build_logging_dict()
    except ComponentConfigurationError as exc:
        return [Error(str(exc), id="django_logging.E046_COMPONENTS")]
    return []
