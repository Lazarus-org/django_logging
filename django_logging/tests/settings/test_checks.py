from unittest.mock import patch

import pytest
from django.core.checks import Error
from django.conf import settings
from django_logging.settings.checks import check_logging_settings


@pytest.fixture
def reset_settings():
    """Fixture to reset Django settings after each test."""
    original_settings = settings.DJANGO_LOGGING
    yield
    settings.DJANGO_LOGGING = original_settings


def test_valid_logging_settings(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_DIR": "logs",
        "LOG_FILE_LEVELS": ["DEBUG", "INFO", "ERROR"],
        "LOG_FILE_FORMATS": {"DEBUG": "%(levelname)s: %(message)s"},
        "LOG_CONSOLE_FORMAT": "%(message)s",
        "LOG_CONSOLE_LEVEL": "DEBUG",
        "LOG_CONSOLE_COLORIZE": True,
        "LOG_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
        "AUTO_INITIALIZATION_ENABLE": True,
        "INITIALIZATION_MESSAGE_ENABLE": True,
        "LOG_EMAIL_NOTIFIER": {
            "ENABLE": True,
            "NOTIFY_ERROR": True,
            "NOTIFY_CRITICAL": False,
            "USE_TEMPLATE": True,
            "LOG_FORMAT": 1,
        },
    }
    errors = check_logging_settings(None)
    assert not errors


def test_invalid_log_dir(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_DIR": 1,
    }
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E001_LOG_DIR" for error in errors)


def test_invalid_log_file_levels(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_FILE_LEVELS": ["invalid"],
    }
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E007_LOG_FILE_LEVELS" for error in errors)


def test_invalid_log_file_formats(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_FILE_FORMATS": {
            "DEBUG": "%(levelname)s: %(invalid)s",
            "invalid": "%(message)s",
        },
    }
    errors = check_logging_settings(None)
    assert any(
        error.id == "django_logging.E011_LOG_FILE_FORMATS['DEBUG']" for error in errors
    )
    assert any(error.id == "django_logging.E019_LOG_FILE_FORMATS" for error in errors)

    settings.DJANGO_LOGGING = {"LOG_FILE_FORMATS": ["invalid type"]}
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E020_LOG_FILE_FORMATS" for error in errors)


def test_invalid_log_console_format(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_CONSOLE_FORMAT": "invalid",
    }
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E010_LOG_CONSOLE_FORMAT" for error in errors)


def test_invalid_log_console_level(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_CONSOLE_LEVEL": 10,
    }
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E006_LOG_CONSOLE_LEVEL" for error in errors)


def test_invalid_log_console_colorize(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_CONSOLE_COLORIZE": "not_a_boolean",
    }
    errors = check_logging_settings(None)
    assert any(
        error.id == "django_logging.E014_LOG_CONSOLE_COLORIZE" for error in errors
    )


def test_invalid_log_date_format(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_DATE_FORMAT": "%invalid_format",
    }
    errors = check_logging_settings(None)
    assert any(error.id == "django_logging.E016_LOG_DATE_FORMAT" for error in errors)


def test_invalid_auto_initialization_enable(reset_settings):
    settings.DJANGO_LOGGING = {
        "AUTO_INITIALIZATION_ENABLE": "not_a_boolean",
    }
    errors = check_logging_settings(None)
    assert any(
        error.id == "django_logging.E014_AUTO_INITIALIZATION_ENABLE" for error in errors
    )


def test_invalid_initialization_message_enable(reset_settings):
    settings.DJANGO_LOGGING = {
        "INITIALIZATION_MESSAGE_ENABLE": "not_a_boolean",
    }
    errors = check_logging_settings(None)
    assert any(
        error.id == "django_logging.E014_INITIALIZATION_MESSAGE_ENABLE"
        for error in errors
    )


def test_invalid_log_email_notifier(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_EMAIL_NOTIFIER": {
            "ENABLE": "not_a_boolean",
        },
    }
    errors = check_logging_settings(None)
    assert any(
        error.id == "django_logging.E018_LOG_EMAIL_NOTIFIER['ENABLE']"
        for error in errors
    )


def test_missing_email_settings(reset_settings):
    settings.DJANGO_LOGGING = {
        "LOG_EMAIL_NOTIFIER": {
            "ENABLE": True,
        },
    }
    # Mocking check_email_settings to return errors
    with patch("django_logging.settings.checks.check_email_settings") as mock_check:
        mock_check.return_value = [
            Error("EMAIL_BACKEND not set.", id="django_logging.E010_EMAIL_SETTINGS")
        ]
        errors = check_logging_settings(None)
        assert any(error.id == "django_logging.E010_EMAIL_SETTINGS" for error in errors)
