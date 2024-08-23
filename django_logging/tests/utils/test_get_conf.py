import pytest
from unittest.mock import patch
from django.conf import settings
from django_logging.utils.get_conf import (
    get_config,
    use_email_notifier_template,
    is_auto_initialization_enabled,
    is_initialization_message_enabled,
)


@pytest.fixture
def mock_settings():
    """Fixture to mock Django settings."""
    mock_settings = {
        "DJANGO_LOGGING": {
            "LOG_FILE_LEVELS": ["DEBUG", "INFO"],
            "LOG_DIR": "/custom/log/dir",
            "LOG_FILE_FORMATS": {
                "DEBUG": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "LOG_CONSOLE_LEVEL": "WARNING",
            "LOG_CONSOLE_FORMAT": "%(levelname)s - %(message)s",
            "LOG_CONSOLE_COLORIZE": True,
            "LOG_DATE_FORMAT": "%Y-%m-%d",
            "LOG_EMAIL_NOTIFIER": {
                "ENABLE": True,
                "NOTIFY_ERROR": True,
                "NOTIFY_CRITICAL": False,
                "LOG_FORMAT": "custom_format",
            },
        }
    }
    with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
        yield mock_settings


def test_get_conf(mock_settings):
    expected = [
        ["DEBUG", "INFO"],  # log_levels
        "/custom/log/dir",  # log_dir
        {
            "DEBUG": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },  # log_file_formats
        "WARNING",  # console_level
        "%(levelname)s - %(message)s",  # console_format
        True,  # colorize_console
        "%Y-%m-%d",  # log_date_format
        True,  # log_email_notifier_enable
        ["ERROR", None],  # log_email_notifier_log_levels
        "custom_format",  # log_email_notifier_log_format
    ]
    result = get_config()
    assert result == expected


def test_use_email_notifier_template(mock_settings):
    # By default, USE_TEMPLATE is True
    assert use_email_notifier_template() is True

    # Test with USE_TEMPLATE set to False
    mock_settings["DJANGO_LOGGING"]["LOG_EMAIL_NOTIFIER"]["USE_TEMPLATE"] = False
    with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
        assert use_email_notifier_template() is False


def test_is_auto_initialization_enabled(mock_settings):
    # By default, AUTO_INITIALIZATION_ENABLE is True
    assert is_auto_initialization_enabled() is True

    # Test with AUTO_INITIALIZATION_ENABLE set to False
    mock_settings["DJANGO_LOGGING"]["AUTO_INITIALIZATION_ENABLE"] = False
    with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
        assert is_auto_initialization_enabled() is False


def test_is_initialization_message_enabled(mock_settings):
    # By default, INITIALIZATION_MESSAGE_ENABLE is True
    assert is_initialization_message_enabled() is True

    # Test with INITIALIZATION_MESSAGE_ENABLE set to False
    mock_settings["DJANGO_LOGGING"]["INITIALIZATION_MESSAGE_ENABLE"] = False
    with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
        assert is_initialization_message_enabled() is False
