import sys
from typing import Generator, List
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.checks import Error

from django_logging.settings.checks import check_logging_settings
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.settings,
    pytest.mark.settings_checks,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestChecks:

    def test_valid_logging_settings(self, reset_settings: None) -> None:
        """
        Test that valid logging settings do not produce any errors.

        This test verifies that when all logging settings are properly configured,
        the `check_logging_settings` function does not return any errors.

        Asserts:
        -------
        - No errors are returned by `check_logging_settings`.
        """
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
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert not errors

    def test_invalid_log_dir(self, reset_settings: None) -> None:
        """
        Test invalid LOG_DIR setting.

        This test checks that when `LOG_DIR` is set to an invalid type (e.g., an integer),
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E001_LOG_DIR` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_DIR": 1,
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(error.id == "django_logging.E001_LOG_DIR" for error in errors)

    def test_invalid_log_file_levels(self, reset_settings: None) -> None:
        """
        Test invalid LOG_FILE_LEVELS setting.

        This test checks that when `LOG_FILE_LEVELS` contains invalid log levels,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E007_LOG_FILE_LEVELS` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_FILE_LEVELS": ["invalid"],
        }
        errors = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E007_LOG_FILE_LEVELS" for error in errors
        )

    def test_invalid_log_file_formats(self, reset_settings: None) -> None:
        """
        Test invalid LOG_FILE_FORMATS setting.

        This test checks for various invalid configurations in `LOG_FILE_FORMATS`
        and ensures that the appropriate errors are returned.

        Asserts:
        -------
        - Errors with the IDs `django_logging.E011_LOG_FILE_FORMATS['DEBUG']` and `django_logging.E019_LOG_FILE_FORMATS` are returned for invalid formats.
        - An error with the ID `django_logging.E020_LOG_FILE_FORMATS` is returned for invalid type.
        """
        settings.DJANGO_LOGGING = {
            "LOG_FILE_FORMATS": {
                "DEBUG": "%(levelname)s: %(invalid)s",
                "invalid": "%(message)s",
            },
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E011_LOG_FILE_FORMATS['DEBUG']"
            for error in errors
        )
        assert any(
            error.id == "django_logging.E019_LOG_FILE_FORMATS" for error in errors
        )

        settings.DJANGO_LOGGING = {"LOG_FILE_FORMATS": ["invalid type"]}
        errors = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E020_LOG_FILE_FORMATS" for error in errors
        )

    def test_invalid_log_console_format(self, reset_settings: None) -> None:
        """
        Test invalid LOG_CONSOLE_FORMAT setting.

        This test checks that when `LOG_CONSOLE_FORMAT` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E010_LOG_CONSOLE_FORMAT` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_CONSOLE_FORMAT": "invalid",
        }
        errors = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E010_LOG_CONSOLE_FORMAT" for error in errors
        )

    def test_invalid_log_console_level(self, reset_settings: None) -> None:
        """
        Test invalid LOG_CONSOLE_LEVEL setting.

        This test checks that when `LOG_CONSOLE_LEVEL` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E006_LOG_CONSOLE_LEVEL` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_CONSOLE_LEVEL": 10,
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E006_LOG_CONSOLE_LEVEL" for error in errors
        )

    def test_invalid_log_console_colorize(self, reset_settings: None) -> None:
        """
        Test invalid LOG_CONSOLE_COLORIZE setting.

        This test checks that when `LOG_CONSOLE_COLORIZE` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E014_LOG_CONSOLE_COLORIZE` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_CONSOLE_COLORIZE": "not_a_boolean",
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E014_LOG_CONSOLE_COLORIZE" for error in errors
        )

    def test_invalid_log_date_format(self, reset_settings: None) -> None:
        """
        Test invalid LOG_DATE_FORMAT setting.

        This test checks that when `LOG_DATE_FORMAT` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E016_LOG_DATE_FORMAT` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_DATE_FORMAT": "%invalid_format",
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E016_LOG_DATE_FORMAT" for error in errors
        )

    def test_invalid_auto_initialization_enable(self, reset_settings: None) -> None:
        """
        Test invalid AUTO_INITIALIZATION_ENABLE setting.

        This test checks that when `AUTO_INITIALIZATION_ENABLE` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E014_AUTO_INITIALIZATION_ENABLE` is returned.
        """
        settings.DJANGO_LOGGING = {
            "AUTO_INITIALIZATION_ENABLE": "not_a_boolean",
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E014_AUTO_INITIALIZATION_ENABLE"
            for error in errors
        )

    def test_invalid_initialization_message_enable(self, reset_settings: None) -> None:
        """
        Test invalid INITIALIZATION_MESSAGE_ENABLE setting.

        This test checks that when `INITIALIZATION_MESSAGE_ENABLE` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E014_INITIALIZATION_MESSAGE_ENABLE` is returned.
        """
        settings.DJANGO_LOGGING = {
            "INITIALIZATION_MESSAGE_ENABLE": "not_a_boolean",
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E014_INITIALIZATION_MESSAGE_ENABLE"
            for error in errors
        )

    def test_invalid_log_email_notifier(self, reset_settings: None) -> None:
        """
        Test invalid LOG_EMAIL_NOTIFIER setting.

        This test checks that when `LOG_EMAIL_NOTIFIER['ENABLE']` is set to an invalid value,
        the appropriate error is returned.

        Asserts:
        -------
        - An error with the ID `django_logging.E018_LOG_EMAIL_NOTIFIER['ENABLE']` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_EMAIL_NOTIFIER": {
                "ENABLE": "not_a_boolean",
            },
        }
        errors: List[Error] = check_logging_settings(None)  # type: ignore
        assert any(
            error.id == "django_logging.E018_LOG_EMAIL_NOTIFIER['ENABLE']"
            for error in errors
        )

    def test_missing_email_settings(self, reset_settings: None) -> None:
        """
        Test missing email settings when LOG_EMAIL_NOTIFIER is enabled.

        This test checks that when `LOG_EMAIL_NOTIFIER['ENABLE']` is set to True,
        but required email settings are missing, the appropriate error is returned.

        Mocks:
        ------
        - Mock the `check_email_settings` function to simulate missing email settings.

        Asserts:
        -------
        - An error with the ID `django_logging.E010_EMAIL_SETTINGS` is returned.
        """
        settings.DJANGO_LOGGING = {
            "LOG_EMAIL_NOTIFIER": {
                "ENABLE": True,
            },
        }
        with patch("django_logging.settings.checks.check_email_settings") as mock_check:
            mock_check.return_value = [
                Error("EMAIL_BACKEND not set.", id="django_logging.E010_EMAIL_SETTINGS")
            ]
            errors: List[Error] = check_logging_settings(None)  # type: ignore
            assert any(
                error.id == "django_logging.E010_EMAIL_SETTINGS" for error in errors
            )
