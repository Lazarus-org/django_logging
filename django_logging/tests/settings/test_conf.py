import pytest
from unittest import mock
import os

from django_logging.settings.conf import LogConfig, LogManager
from django_logging.constants import FORMAT_OPTIONS


@pytest.fixture
def log_config():
    return LogConfig(
        log_levels=["INFO", "WARNING", "ERROR"],
        log_dir="/tmp/logs",
        log_file_formats={"INFO": 1, "WARNING": None, "ERROR": "%(message)s"},
        console_level="INFO",
        console_format=1,
        colorize_console=False,
        log_date_format="%Y-%m-%d %H:%M:%S",
        log_email_notifier_enable=True,
        log_email_notifier_log_levels=["ERROR"],
        log_email_notifier_log_format=1,
    )


@pytest.fixture
def log_manager(log_config):
    return LogManager(log_config)


def test_resolve_format():
    # Test with int format option
    resolved_format_option = LogConfig.resolve_format(1, use_colors=False)
    resolved_none_format = LogConfig.resolve_format(None, use_colors=False)

    assert resolved_format_option == FORMAT_OPTIONS[1]
    assert resolved_none_format

    # Test with str format option
    resolved_format = LogConfig.resolve_format("%(message)s", use_colors=False)
    assert resolved_format == "%(message)s"

    # Test with color enabled
    resolved_format = LogConfig.resolve_format("%(message)s", use_colors=True)
    assert resolved_format == "%(message)s"


def test_remove_ansi_escape_sequences():
    ansi_string = "\x1b[31mERROR\x1b[0m"
    clean_string = LogConfig.remove_ansi_escape_sequences(ansi_string)
    assert clean_string == "ERROR"


def test_create_log_files(log_manager):
    with mock.patch("os.makedirs") as makedirs_mock, mock.patch(
        "os.path.exists"
    ) as path_exists_mock, mock.patch("builtins.open", mock.mock_open()) as open_mock:
        # Mock path_exists to return False so that it always attempts to create the file
        path_exists_mock.return_value = False
        log_manager.log_config.log_levels = ["INFO", "ERROR"]
        log_manager.log_files = {}

        log_manager.create_log_files()

        # Check that the directories were created
        makedirs_mock.assert_called_with("/tmp/logs", exist_ok=True)

        # Verify the log files are created
        assert open_mock.call_count == len(log_manager.log_config.log_levels)

        # Verify file creation paths
        for log_level in log_manager.log_config.log_levels:
            expected_file_path = os.path.join("/tmp/logs", f"{log_level.lower()}.log")
            open_mock.assert_any_call(expected_file_path, "w")

            log_manager.log_files[log_level] = expected_file_path


def test_set_conf(log_manager):
    with mock.patch("logging.config.dictConfig") as dictConfig_mock:
        log_manager.create_log_files()
        log_manager.set_conf()

        # Check that the logging config was set
        assert dictConfig_mock.called

        config = dictConfig_mock.call_args[0][0]

        # Verify the structure of the config
        assert "version" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        assert "root" in config

        # Check formatters
        assert "info" in config["formatters"]
        assert "error" in config["formatters"]
        assert "console" in config["formatters"]
        assert "email" in config["formatters"]

        # Check handlers
        assert "info" in config["handlers"]
        assert "error" in config["handlers"]
        assert "console" in config["handlers"]
        assert "email_error" in config["handlers"]

        # Check loggers
        assert "info" in config["loggers"]
        assert "error" in config["loggers"]

        # Check the root logger
        assert "handlers" in config["root"]
        assert "disable_existing_loggers" in config


def test_log_manager_get_log_file(log_manager):
    with mock.patch("os.makedirs"), mock.patch("builtins.open", mock.mock_open()):

        log_manager.create_log_files()

        # Check retrieving the log files
        assert log_manager.get_log_file("INFO") == "/tmp/logs\\info.log"
        assert log_manager.get_log_file("ERROR") == "/tmp/logs\\error.log"

        # Check for a non-existent log level
        assert log_manager.get_log_file("DEBUG") is None
