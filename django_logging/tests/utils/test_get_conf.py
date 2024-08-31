import sys
from typing import Dict
from unittest.mock import patch

import pytest
from django.conf import settings

from django_logging.utils.get_conf import (
    get_config,
    is_auto_initialization_enabled,
    is_initialization_message_enabled,
    use_email_notifier_template,
)
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_get_conf,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestGetConf:

    def test_get_conf(self, mock_settings: Dict) -> None:
        """
        Test that the `get_config` function returns the correct configuration values.

        This test verifies that the `get_config` function extracts and returns the correct
        configuration values from the Django settings.

        Mocks:
        ------
        - `django.conf.settings` to provide mock configuration values.

        Asserts:
        -------
        - The returned configuration matches the expected values for logging levels, directory,
          file formats, console settings, email notifier settings, etc.
        """
        expected = {
            "log_levels": ["DEBUG", "INFO"],
            "log_dir": "/custom/log/dir",
            "log_file_formats": {
                "DEBUG": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "console_level": "WARNING",
            "console_format": "%(levelname)s - %(message)s",
            "colorize_console": True,
            "log_date_format": "%Y-%m-%d",
            "log_email_notifier_enable": True,
            "log_email_notifier_log_levels": ["ERROR", None],
            "log_email_notifier_log_format": "custom_format",
        }
        print(expected)
        result = get_config()
        assert result == expected

        result = get_config(extra_info=True)

        expected_extra = {
            "log_levels": ["DEBUG", "INFO"],
            "log_dir": "/custom/log/dir",
            "log_file_formats": {
                "DEBUG": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "console_level": "WARNING",
            "console_format": "%(levelname)s - %(message)s",
            "colorize_console": True,
            "log_date_format": "%Y-%m-%d",
            "log_email_notifier_enable": True,
            "log_email_notifier_log_levels": ["ERROR", None],
            "log_email_notifier_log_format": "custom_format",
            "log_email_notifier": {
                "ENABLE": True,
                "NOTIFY_ERROR": True,
                "NOTIFY_CRITICAL": False,
                "LOG_FORMAT": "custom_format",
            },
        }

        assert result == expected_extra

    def test_use_email_notifier_template(self, mock_settings: Dict) -> None:
        """
        Test that the `use_email_notifier_template` function correctly reads the `USE_TEMPLATE` setting.

        This test verifies that the `use_email_notifier_template` function returns `True` by default,
        and correctly reflects changes to the `USE_TEMPLATE` setting.

        Mocks:
        ------
        - `django.conf.settings` to provide mock configuration values.

        Asserts:
        -------
        - The default return value of `use_email_notifier_template` is `True`.
        - Changing the `USE_TEMPLATE` setting to `False` updates the return value accordingly.
        """
        # By default, USE_TEMPLATE is True
        assert use_email_notifier_template() is True

        # Test with USE_TEMPLATE set to False
        mock_settings["DJANGO_LOGGING"]["LOG_EMAIL_NOTIFIER"]["USE_TEMPLATE"] = False
        with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
            assert use_email_notifier_template() is False

    def test_is_auto_initialization_enabled(self, mock_settings: Dict) -> None:
        """
        Test that the `is_auto_initialization_enabled` function correctly reads the `AUTO_INITIALIZATION_ENABLE` setting.

        This test verifies that the `is_auto_initialization_enabled` function returns `True` by default,
        and correctly reflects changes to the `AUTO_INITIALIZATION_ENABLE` setting.

        Mocks:
        ------
        - `django.conf.settings` to provide mock configuration values.

        Asserts:
        -------
        - The default return value of `is_auto_initialization_enabled` is `True`.
        - Changing the `AUTO_INITIALIZATION_ENABLE` setting to `False` updates the return value accordingly.
        """
        # By default, AUTO_INITIALIZATION_ENABLE is True
        assert is_auto_initialization_enabled() is True

        # Test with AUTO_INITIALIZATION_ENABLE set to False
        mock_settings["DJANGO_LOGGING"]["AUTO_INITIALIZATION_ENABLE"] = False
        with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
            assert is_auto_initialization_enabled() is False

    def test_is_initialization_message_enabled(self, mock_settings: Dict) -> None:
        """
        Test that the `is_initialization_message_enabled` function correctly reads the `INITIALIZATION_MESSAGE_ENABLE` setting.

        This test verifies that the `is_initialization_message_enabled` function returns `True` by default,
        and correctly reflects changes to the `INITIALIZATION_MESSAGE_ENABLE` setting.

        Mocks:
        ------
        - `django.conf.settings` to provide mock configuration values.

        Asserts:
        -------
        - The default return value of `is_initialization_message_enabled` is `True`.
        - Changing the `INITIALIZATION_MESSAGE_ENABLE` setting to `False` updates the return value accordingly.
        """
        # By default, INITIALIZATION_MESSAGE_ENABLE is True
        assert is_initialization_message_enabled() is True

        # Test with INITIALIZATION_MESSAGE_ENABLE set to False
        mock_settings["DJANGO_LOGGING"]["INITIALIZATION_MESSAGE_ENABLE"] = False
        with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
            assert is_initialization_message_enabled() is False
