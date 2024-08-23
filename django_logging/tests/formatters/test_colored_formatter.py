import logging
import pytest
from unittest.mock import patch
from django_logging.formatters import ColorizedFormatter


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


@pytest.fixture
def formatter():
    """Fixture to create a ColoredFormatter instance with a specific format."""
    return ColorizedFormatter(fmt="%(levelname)s: %(message)s")


@patch(
    "django_logging.formatters.colored_formatter.colorize_log_format", autospec=True
)
@patch(
    "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
    side_effect=lambda fmt: fmt,
)
def test_format_applies_colorization(
    mock_remove_ansi, mock_colorize, formatter, log_record
):
    """Test that the format method applies colorization."""
    # Mock the colorize_log_format to return a predictable format
    mock_colorize.return_value = "%(levelname)s: %(message)s"

    formatter.format(log_record)

    # Ensuring colorization should have been triggered
    mock_colorize.assert_called_once_with(
        "%(levelname)s: %(message)s", log_record.levelname
    )


@patch(
    "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
    side_effect=lambda fmt: fmt,
)
def test_format_resets_to_original_format(mock_remove_ansi, formatter, log_record):
    """Test that the format method resets the format string after formatting."""
    original_format = formatter._style._fmt
    formatter.format(log_record)
    assert (
        formatter._style._fmt == original_format
    ), f"Expected format string to reset to original format, but got {formatter._style._fmt}"


@patch(
    "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
    side_effect=lambda fmt: fmt,
)
def test_format_returns_formatted_output(formatter, log_record):
    """Test that the format method returns the correctly formatted output."""
    expected_output = f"{logging.getLevelName(log_record.levelno)}: {log_record.msg}"
    formatted_output = formatter.format(log_record)

    # Directly comparing the output assuming it might include color codes
    assert formatted_output.startswith(
        f"DEBUG: Test message"
    ), f"Expected formatted output to start with '{expected_output}', but got '{formatted_output}'"
