from unittest.mock import patch, MagicMock
import os
from django_logging.constants.ansi_colors import AnsiColors

from django_logging.utils.set_conf import set_config


@patch("django_logging.utils.set_conf.LogConfig")
@patch("django_logging.utils.set_conf.LogManager")
@patch("django_logging.utils.set_conf.is_auto_initialization_enabled")
@patch("django_logging.utils.set_conf.is_initialization_message_enabled")
@patch("logging.getLogger")
@patch("django_logging.utils.get_conf.get_config")
def test_set_config_success(
    mock_get_conf,
    mock_get_logger,
    mock_is_initialization_message_enabled,
    mock_is_auto_initialization_enabled,
    mock_LogManager,
    mock_LogConfig,
):
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
    mock_is_auto_initialization_enabled, mock_LogManager, mock_LogConfig
):
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
    mock_is_auto_initialization_enabled, mock_LogManager, mock_LogConfig
):
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
            f"========================{AnsiColors.RED_BACKGROUND}DJANGO LOGGING{AnsiColors.RESET}"
            f"========================\n"
            f"{AnsiColors.RED}[CONFIGURATION ERROR]{AnsiColors.RESET}"
            f" A configuration issue has been detected.\n"
            "System checks will be run to provide more detailed information.\n"
            "==============================================================\n"
        )
