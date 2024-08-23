import logging
import pytest
from unittest.mock import patch, MagicMock
from django_logging.formatters import ColorizedFormatter


@pytest.fixture
def log_record() -> logging.LogRecord:
    """
    Fixture to create a dummy log record for testing.

    Returns:
    -------
    logging.LogRecord
        A dummy log record with predefined attributes.
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


@pytest.fixture
def formatter() -> ColorizedFormatter:
    """
    Fixture to create a `ColorizedFormatter` instance with a specific format.

    Returns:
    -------
    ColorizedFormatter
        An instance of `ColorizedFormatter` with a predefined format.
    """
    return ColorizedFormatter(fmt="%(levelname)s: %(message)s")


@patch("django_logging.formatters.colored_formatter.colorize_log_format", autospec=True)
@patch(
    "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
    side_effect=lambda fmt: fmt,
)
def test_format_applies_colorization(
    mock_remove_ansi: MagicMock, mock_colorize: MagicMock, formatter: ColorizedFormatter, log_record: logging.LogRecord
) -> None:
    """
    Test that the `format` method of `ColorizedFormatter` applies colorization.

    This test verifies that the `format` method calls the `colorize_log_format`
    function to apply colorization based on the log level.

    Parameters:
    ----------
    mock_remove_ansi : MagicMock
        Mock for `remove_ansi_escape_sequences`.
    mock_colorize : MagicMock
        Mock for `colorize_log_format`.
    formatter : ColorizedFormatter
        The formatter instance being tested.
    log_record : logging.LogRecord
        The dummy log record created by the fixture.

    Asserts:
    -------
    - The `colorize_log_format` function is called once with the correct arguments.
    """
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
def test_format_resets_to_original_format(
        mock_remove_ansi: MagicMock, formatter: ColorizedFormatter, log_record: logging.LogRecord) -> None:
    """
    Test that the `format` method resets the format string to its original state after formatting.

    This test ensures that the formatter's internal format string is not permanently modified
    by the colorization process and is reset to its original value after each log record is formatted.

    Parameters:
    ----------
    mock_remove_ansi : MagicMock
        Mock for `remove_ansi_escape_sequences`.
    formatter : ColorizedFormatter
        The formatter instance being tested.
    log_record : logging.LogRecord
        The dummy log record created by the fixture.

    Asserts:
    -------
    - The formatter's internal format string (`_style._fmt`) matches the original format after formatting.
    """
    original_format = formatter._style._fmt
    formatter.format(log_record)
    assert (
        formatter._style._fmt == original_format
    ), f"Expected format string to reset to original format, but got {formatter._style._fmt}"


@patch(
    "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
    side_effect=lambda fmt: fmt,
)
def test_format_returns_formatted_output(formatter: ColorizedFormatter, log_record: logging.LogRecord) -> None:
    """
    Test that the `format` method returns the correctly formatted log output.

    This test verifies that the formatted output matches the expected structure,
    including the log level name and the log message.

    Parameters:
    ----------
    formatter : ColorizedFormatter
        The formatter instance being tested.
    log_record : logging.LogRecord
        The dummy log record created by the fixture.

    Asserts:
    -------
    - The formatted output starts with the expected log level and message.
    """
    expected_output = f"{logging.getLevelName(log_record.levelno)}: {log_record.msg}"
    formatted_output = formatter.format(log_record)

    # Directly comparing the output assuming it might include color codes
    assert formatted_output.startswith(
        f"DEBUG: Test message"
    ), f"Expected formatted output to start with '{expected_output}', but got '{formatted_output}'"
