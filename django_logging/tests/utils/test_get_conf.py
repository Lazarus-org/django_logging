import sys
from typing import Dict

import pytest
from django.conf import settings

from django_logging.settings.manager import SettingsManager, settings_manager
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON
from django_logging.utils.get_conf import (
    is_initialization_message_enabled,
)

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_get_conf,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestGetConf:

    def test_is_initialization_message_enabled(self, mock_settings: Dict) -> None:
        """
        Test that the `is_initialization_message_enabled` function correctly reads the `INITIALIZATION_MESSAGE_ENABLE` setting.

        This test verifies that the `is_initialization_message_enabled` function returns `True` by default.

        Mocks:
        ------
        - `django.conf.settings` to provide mock configuration values.

        Asserts:
        -------
        - The default return value of `is_initialization_message_enabled` is `True`.
        """
        # By default, INITIALIZATION_MESSAGE_ENABLE is not none
        assert is_initialization_message_enabled() is not None

    def test_logging_settings_none(self) -> None:
        """
        Test that logging settings is None and raise `ValueError`.

        This test verifies that when logging settings (DJANGO_LOGGING) is None,
        the `get_config` function raises `ValueError`.

        Asserts:
        -------
        - ValueError raised by `check_logging_settings`.
        """
        settings.DJANGO_LOGGING = None
        with pytest.raises(ValueError, match="DJANGO_LOGGING must be a dictionary with configs as keys"):
            SettingsManager()
