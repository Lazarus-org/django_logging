import logging
import pytest
from django_logging.filters import LoggingLevelFilter


@pytest.fixture
def log_record() -> logging.LogRecord:
    """
    Fixture to create a dummy log record for testing.

    Returns:
    -------
        logging.LogRecord: A dummy log record with predefined attributes.
    """
    return logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )


def test_logging_level_filter_initialization() -> None:
    """
    Test that the `LoggingLevelFilter` initializes with the correct logging level.

    Asserts:
    -------
        - The `logging_level` attribute of the filter instance is set to the provided logging level.
    """
    filter_instance = LoggingLevelFilter(logging.INFO)
    assert filter_instance.logging_level == logging.INFO, (
        f"Expected logging_level to be {logging.INFO}, "
        f"got {filter_instance.logging_level}"
    )


def test_logging_level_filter_passes_matching_level(
    log_record: logging.LogRecord,
) -> None:
    """
    Test that the `LoggingLevelFilter` passes log records with the matching logging level.

    Args:
    ----
        log_record (logging.LogRecord): A dummy log record created by the fixture.

    Asserts:
    -------
        - The filter method returns True when the log record's level matches the filter's level.
    """
    log_record.levelno = logging.DEBUG
    filter_instance = LoggingLevelFilter(logging.DEBUG)

    assert filter_instance.filter(log_record), (
        f"Expected filter to return True for log level {logging.DEBUG}, " f"got False"
    )


def test_logging_level_filter_blocks_non_matching_level(
    log_record: logging.LogRecord,
) -> None:
    """
    Test that the `LoggingLevelFilter` blocks log records with a non-matching logging level.

    Args:
    ----
        log_record (logging.LogRecord): A dummy log record created by the fixture.

    Asserts:
    -------
        - The filter method returns False when the log record's level does not match the filter's level.
    """
    log_record.levelno = logging.WARNING
    filter_instance = LoggingLevelFilter(logging.ERROR)

    assert not filter_instance.filter(log_record), (
        f"Expected filter to return False for log level {logging.WARNING}, " f"got True"
    )
