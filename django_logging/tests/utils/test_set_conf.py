import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from django_logging.constants.ansi_colors import AnsiColors
from django_logging.utils.set_conf import set_config
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_set_conf,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestSetConf:

    @patch("django_logging.utils.set_conf.LogConfig")
    @patch("django_logging.utils.set_conf.LogManager")
    @patch("django_logging.utils.set_conf.is_auto_initialization_enabled")
    @patch("django_logging.utils.set_conf.is_initialization_message_enabled")
    @patch("logging.getLogger")
    @patch("django_logging.utils.get_conf.get_config")
    def test_set_config_success(
        self,
        mock_get_conf: MagicMock,
        mock_get_logger: MagicMock,
        mock_is_initialization_message_enabled: MagicMock,
        mock_is_auto_initialization_enabled: MagicMock,
        mock_LogManager: MagicMock,
        mock_LogConfig: MagicMock,
    ) -> None:
        """
        Test the successful execution of set_config.

        This test verifies that the set_config function correctly initializes
        LogConfig and LogManager when auto initialization is enabled. It also
        checks that the initialization message is logged if RUN_MAIN is set to "true"
        and initialization messages are enabled.

        Mocks:
        ------
        - `django_logging.utils.get_conf.get_config` to return mock configuration values.
        - `logging.getLogger` to provide a mock logger.
        - `django_logging.utils.set_conf.LogConfig` to simulate LogConfig instantiation.
        - `django_logging.utils.set_conf.LogManager` to simulate LogManager instantiation.
        - `django_logging.utils.set_conf.is_auto_initialization_enabled` to control auto initialization.
        - `django_logging.utils.set_conf.is_initialization_message_enabled` to check if initialization messages are enabled.

        Asserts:
        -------
        - `LogConfig` and `LogManager` are instantiated with the expected arguments.
        - `create_log_files` and `set_conf` methods of `LogManager` are called once.
        - If RUN_MAIN is "true" and initialization messages are enabled, an info log is generated.
        """
        # Mock the configuration
        mock_is_auto_initialization_enabled.return_value = True
        mock_get_conf.return_value = (
            ["DEBUG", "INFO"],
            "/path/to/logs",
            {"DEBUG": 1, "INFO": 2},
            "DEBUG",
            1,
            True,
            "",
            False,
            ["INFO"],
            1,
        )

        # Mock the logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Call the function
        set_config(
            ["DEBUG", "INFO"],
            "/path/to/logs",
            {"DEBUG": 1, "INFO": 2},
            "DEBUG",
            1,
            True,
            "",
            False,
            ["ERROR"],
            1,
        )

        # Check that LogConfig and LogManager are instantiated
        mock_LogConfig.assert_called_once_with(
            ["DEBUG", "INFO"],
            "/path/to/logs",
            {"DEBUG": 1, "INFO": 2},
            "DEBUG",
            1,
            True,
            "",
            False,
            ["ERROR"],
            1,
        )
        mock_LogManager.assert_called_once_with(mock_LogConfig.return_value)

        # Check if create_log_files and set_conf were called
        mock_LogManager.return_value.create_log_files.assert_called_once()
        mock_LogManager.return_value.set_conf.assert_called_once()

        # Ensure initialization message is logged if RUN_MAIN is "true" and initialization message is enabled
        os.environ["RUN_MAIN"] = "true"
        mock_is_initialization_message_enabled.return_value = True
        set_config(
            ["DEBUG", "INFO"],
            "/path/to/logs",
            {"DEBUG": 1, "INFO": 2},
            "DEBUG",
            1,
            True,
            "",
            False,
            ["ERROR"],
            1,
        )
        mock_logger.info.assert_called_once()

    @patch("django_logging.utils.set_conf.LogConfig")
    @patch("django_logging.utils.set_conf.LogManager")
    @patch("django_logging.utils.set_conf.is_auto_initialization_enabled")
    def test_set_config_auto_initialization_disabled(
        self,
        mock_is_auto_initialization_enabled: MagicMock,
        mock_LogManager: MagicMock,
        mock_LogConfig: MagicMock,
    ) -> None:
        """
        Test that LogConfig and LogManager are not instantiated when auto initialization is disabled.

        This test verifies that when auto initialization is disabled, the set_config function
        does not instantiate `LogConfig` or `LogManager`.

        Mocks:
        ------
        - `django_logging.utils.set_conf.is_auto_initialization_enabled` to return False.
        - `django_logging.utils.set_conf.LogConfig` to simulate LogConfig instantiation.
        - `django_logging.utils.set_conf.LogManager` to simulate LogManager instantiation.

        Asserts:
        -------
        - `LogConfig` and `LogManager` are not instantiated.
        """
        mock_is_auto_initialization_enabled.return_value = False

        # Call the function
        set_config(
            ["DEBUG", "INFO"],
            "/path/to/logs",
            {"DEBUG": 1, "INFO": 2},
            "DEBUG",
            1,
            True,
            "",
            False,
            ["ERROR"],
            1,
        )

        # Verify that LogConfig and LogManager are not instantiated
        mock_LogConfig.assert_not_called()
        mock_LogManager.assert_not_called()

    @patch("django_logging.utils.set_conf.LogConfig")
    @patch("django_logging.utils.set_conf.LogManager")
    @patch("django_logging.utils.set_conf.is_auto_initialization_enabled")
    def test_set_config_exception_handling(
        self,
        mock_is_auto_initialization_enabled: MagicMock,
        mock_LogManager: MagicMock,
        mock_LogConfig: MagicMock,
    ) -> None:
        """
        Test that set_config handles exceptions and logs a warning message.

        This test verifies that if an exception occurs during the instantiation of
        `LogManager`, a warning message is logged indicating a configuration error.

        Mocks:
        ------
        - `django_logging.utils.set_conf.is_auto_initialization_enabled` to return True.
        - `django_logging.utils.set_conf.LogManager` to raise a ValueError.
        - `logging.warning` to capture the warning message.

        Asserts:
        -------
        - A warning message indicating a configuration error is logged.
        """
        colors = AnsiColors()
        mock_is_auto_initialization_enabled.return_value = True
        mock_LogManager.side_effect = ValueError("Invalid configuration")

        with patch("logging.warning") as mock_warning:
            set_config(
                ["DEBUG", "INFO"],
                "/path/to/logs",
                {"DEBUG": 1, "INFO": 2},
                "DEBUG",
                1,
                True,
                "",
                False,
                ["ERROR"],
                1,
            )
            mock_warning.assert_called_once_with(
                "\n"
                "========================%sDJANGO LOGGING%s"
                "========================\n"
                "%s[CONFIGURATION ERROR]%s"
                " A configuration issue has been detected.\n"
                "System checks will be run to provide more detailed information.\n"
                "==============================================================\n",
                colors.RED_BACKGROUND,
                colors.RESET,
                colors.RED,
                colors.RESET,
            )
