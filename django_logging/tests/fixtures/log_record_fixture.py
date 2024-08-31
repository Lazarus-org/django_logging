from logging import DEBUG, ERROR, LogRecord

import pytest


@pytest.fixture
def debug_log_record() -> LogRecord:
    """
    Fixture to create a dummy log record for testing.

    Returns:
    -------
        logging.LogRecord: A dummy log record with predefined attributes.
    """
    return LogRecord(
        name="test",
        level=DEBUG,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )


@pytest.fixture
def error_log_record() -> LogRecord:
    """
    Fixture to create a dummy log record for testing.

    Returns:
    -------
        logging.LogRecord: A dummy log record with predefined attributes.
    """
    return LogRecord(
        name="test",
        level=ERROR,
        pathname=__file__,
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
