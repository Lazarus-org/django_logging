import logging
import pytest
from django_logging.filters import LoggingLevelFilter


@pytest.fixture
def log_record():
    """Fixture to create a dummy log record."""
    return logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )


def test_logging_level_filter_initialization():
    """Test that LoggingLevelFilter initializes with the correct logging level."""
    filter_instance = LoggingLevelFilter(logging.INFO)
    assert filter_instance.logging_level == logging.INFO, (
        f"Expected logging_level to be {logging.INFO}, "
        f"got {filter_instance.logging_level}"
    )


def test_logging_level_filter_passes_matching_level(log_record):
    """Test that the filter passes log records with the matching level."""
    log_record.levelno = logging.DEBUG
    filter_instance = LoggingLevelFilter(logging.DEBUG)

    assert filter_instance.filter(log_record), (
        f"Expected filter to return True for log level {logging.DEBUG}, " f"got False"
    )


def test_logging_level_filter_blocks_non_matching_level(log_record):
    """Test that the filter blocks log records with a non-matching level."""
    log_record.levelno = logging.WARNING
    filter_instance = LoggingLevelFilter(logging.ERROR)

    assert not filter_instance.filter(log_record), (
        f"Expected filter to return False for log level {logging.WARNING}, " f"got True"
    )
