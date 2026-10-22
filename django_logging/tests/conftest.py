from django_logging.tests.setup import configure_django_settings

# Configure Django before importing fixtures that import application models.
configure_django_settings()

from django_logging.tests.fixtures import (
    admin_email_mock_settings,
    client,
    colored_formatter,
    debug_log_record,
    email_handler,
    email_mock_settings,
    error_log_record,
    error_with_exc_log_record,
    flat_formatter,
    get_response,
    json_formatter,
    log_config,
    log_dir_with_rotated_files,
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
    setup_users,
    temp_json_log_directory,
    temp_log_directory,
    temp_xml_log_directory,
    xml_formatter,
)
