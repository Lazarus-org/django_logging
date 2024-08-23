import pytest
from unittest import mock
import os

from django_logging.settings.conf import LogConfig, LogManager
from django_logging.constants import FORMAT_OPTIONS


@pytest.fixture
def log_config() -> LogConfig:
    """
    Fixture to provide a default LogConfig instance.

    This fixture sets up a LogConfig object with sample values for various logging
    configuration options, including log levels, log directory, formats, and email notifier settings.

    Returns:
    -------
    LogConfig
        An instance of the LogConfig class initialized with sample values.
    """
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
def log_manager(log_config) -> LogManager:
    """
    Fixture to provide a LogManager instance initialized with a LogConfig.

    This fixture sets up a LogManager object using the provided LogConfig instance
    for managing logging configurations and operations.

    Returns:
    -------
    LogManager
        An instance of the LogManager class initialized with the provided LogConfig.
    """
    return LogManager(log_config)


def test_resolve_format() -> None:
    """
    Test resolution of format options in LogConfig.

    This test verifies that the `resolve_format` method of LogConfig correctly
    resolves format options based on different input types, including integer
    format options and string formats. It also checks the behavior with colorization
    enabled and disabled.

    Asserts:
    -------
    - The integer format option resolves to the expected value from FORMAT_OPTIONS.
    - The None format resolves to an appropriate default.
    - String formats resolve to themselves.
    """
    resolved_format_option = LogConfig.resolve_format(1, use_colors=False)
    resolved_none_format = LogConfig.resolve_format(None, use_colors=False)

    assert resolved_format_option == FORMAT_OPTIONS[1]
    assert resolved_none_format

    resolved_format = LogConfig.resolve_format("%(message)s", use_colors=False)
    assert resolved_format == "%(message)s"

    resolved_format = LogConfig.resolve_format("%(message)s", use_colors=True)
    assert resolved_format == "%(message)s"


def test_remove_ansi_escape_sequences() -> None:
    """
    Test removal of ANSI escape sequences.

    This test verifies that the `remove_ansi_escape_sequences` method correctly
    removes ANSI escape sequences from a string, resulting in a clean output.

    Asserts:
    -------
    - The ANSI escape sequences are removed, leaving only the clean string.
    """
    ansi_string = "\x1b[31mERROR\x1b[0m"
    clean_string = LogConfig.remove_ansi_escape_sequences(ansi_string)
    assert clean_string == "ERROR"


def test_create_log_files(log_manager: LogManager) -> None:
    """
    Test creation of log files.

    This test checks that the `create_log_files` method of LogManager correctly
    creates log files for each log level and ensures that the necessary directories
    are created. It also verifies that the open function is called the expected number
    of times with the correct file paths.

    Mocks:
    ------
    - `os.makedirs` to ensure directory creation.
    - `os.path.exists` to simulate file existence checks.
    - `builtins.open` to simulate file creation.

    Asserts:
    -------
    - The `os.makedirs` function is called to create the log directory.
    - The `open` function is called for each log level with the expected file path.
    """
    with mock.patch("os.makedirs") as makedirs_mock, mock.patch(
        "os.path.exists"
    ) as path_exists_mock, mock.patch("builtins.open", mock.mock_open()) as open_mock:
        path_exists_mock.return_value = False
        log_manager.log_config.log_levels = ["INFO", "ERROR"]
        log_manager.log_files = {}

        log_manager.create_log_files()

        makedirs_mock.assert_called_with("/tmp/logs", exist_ok=True)

        assert open_mock.call_count == len(log_manager.log_config.log_levels)

        for log_level in log_manager.log_config.log_levels:
            expected_file_path = os.path.join("/tmp/logs", f"{log_level.lower()}.log")
            open_mock.assert_any_call(expected_file_path, "w")

            log_manager.log_files[log_level] = expected_file_path


def test_set_conf(log_manager: LogManager) -> None:
    """
    Test setting up logging configuration.

    This test verifies that the `set_conf` method of LogManager correctly configures
    logging settings using `logging.config.dictConfig`. It checks the structure of the
    configuration dictionary to ensure all necessary components are present.

    Mocks:
    ------
    - `logging.config.dictConfig` to simulate setting the logging configuration.

    Asserts:
    -------
    - The `dictConfig` function is called.
    - The configuration dictionary contains expected keys and structures.
    """
    with mock.patch("logging.config.dictConfig") as dictConfig_mock:
        log_manager.create_log_files()
        log_manager.set_conf()

        assert dictConfig_mock.called

        config = dictConfig_mock.call_args[0][0]

        assert "version" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        assert "root" in config

        assert "info" in config["formatters"]
        assert "error" in config["formatters"]
        assert "console" in config["formatters"]
        assert "email" in config["formatters"]

        assert "info" in config["handlers"]
        assert "error" in config["handlers"]
        assert "console" in config["handlers"]
        assert "email_error" in config["handlers"]

        assert "info" in config["loggers"]
        assert "error" in config["loggers"]

        assert "handlers" in config["root"]
        assert "disable_existing_loggers" in config


def test_log_manager_get_log_file(log_manager: LogManager) -> None:
    """
    Test retrieval of log file paths.

    This test verifies that the `get_log_file` method of LogManager correctly returns
    the file path for existing log levels and returns None for non-existent log levels.

    Mocks:
    ------
    - `os.makedirs` and `builtins.open` to simulate log file creation.

    Asserts:
    -------
    - The correct file path is returned for existing log levels.
    - None is returned for a non-existent log level.
    """
    with mock.patch("os.makedirs"), mock.patch("builtins.open", mock.mock_open()):

        log_manager.create_log_files()

        assert log_manager.get_log_file("INFO") == "/tmp/logs\\info.log"
        assert log_manager.get_log_file("ERROR") == "/tmp/logs\\error.log"

        assert log_manager.get_log_file("DEBUG") is None
