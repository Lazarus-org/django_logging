from django_logging.tests.fixtures import (
    admin_email_mock_settings,
    colored_formatter,
    debug_log_record,
    email_handler,
    email_mock_settings,
    error_log_record,
    get_response,
    log_config,
    log_manager,
    magic_mock_logger,
    mock_email_settings,
    mock_logger,
    mock_settings,
    mock_smtp,
    notifier_mock_logger,
    request_factory,
    request_middleware,
    reset_settings,
)
from django_logging.tests.settings_configuration import configure_django_settings

configure_django_settings()
