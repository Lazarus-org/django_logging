import pytest

from django_logging.settings.conf import LogConfig, LogManager


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
        log_file_formats={"INFO": 1, "WARNING": None, "ERROR": "%(message)s"},  # type: ignore
        console_level="INFO",
        console_format=1,
        colorize_console=False,
        log_date_format="%Y-%m-%d %H:%M:%S",
        log_email_notifier_enable=True,
        log_email_notifier_log_levels=["ERROR"],
        log_email_notifier_log_format=1,
    )


@pytest.fixture
def log_manager(log_config: LogConfig) -> LogManager:
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
