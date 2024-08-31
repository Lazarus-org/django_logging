import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from django_logging.formatters import ColoredFormatter
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.formatters,
    pytest.mark.colored_formatter,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestColoredFormatter:

    @patch(
        "django_logging.formatters.colored_formatter.colorize_log_format", autospec=True
    )
    @patch(
        "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
        side_effect=lambda fmt: fmt,
    )
    def test_format_applies_colorization(
        self,
        mock_remove_ansi: MagicMock,
        mock_colorize: MagicMock,
        colored_formatter: ColoredFormatter,
        debug_log_record: logging.LogRecord,
    ) -> None:
        """
        Test that the `format` method of `ColoredFormatter` applies colorization.

        This test verifies that the `format` method calls the `colorize_log_format`
        function to apply colorization based on the log level.

        Parameters:
        ----------
        mock_remove_ansi : MagicMock
            Mock for `remove_ansi_escape_sequences`.
        mock_colorize : MagicMock
            Mock for `colorize_log_format`.
        colored_formatter : ColoredFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The `colorize_log_format` function is called once with the correct arguments.
        """
        # Mock the colorize_log_format to return a predictable format
        mock_colorize.return_value = "%(levelname)s: %(message)s"

        colored_formatter.format(debug_log_record)

        # Ensuring colorization should have been triggered
        mock_colorize.assert_called_once_with(
            "%(levelname)s: %(message)s", debug_log_record.levelname
        )

    @patch(
        "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
        side_effect=lambda fmt: fmt,
    )
    def test_format_resets_to_original_format(
        self,
        mock_remove_ansi: MagicMock,
        colored_formatter: ColoredFormatter,
        debug_log_record: logging.LogRecord,
    ) -> None:
        """
        Test that the `format` method resets the format string to its original state after formatting.

        This test ensures that the formatter's internal format string is not permanently modified
        by the colorization process and is reset to its original value after each log record is formatted.

        Parameters:
        ----------
        mock_remove_ansi : MagicMock
            Mock for `remove_ansi_escape_sequences`.
        colored_formatter : ColoredFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The formatter's internal format string (`_style._fmt`) matches the original format after formatting.
        """
        original_format = colored_formatter._style._fmt
        colored_formatter.format(debug_log_record)
        assert (
            colored_formatter._style._fmt == original_format
        ), f"Expected format string to reset to original format, but got {colored_formatter._style._fmt}"

    @patch(
        "django_logging.settings.conf.LogConfig.remove_ansi_escape_sequences",
        side_effect=lambda fmt: fmt,
    )
    def test_format_returns_formatted_output(
        self, colored_formatter: ColoredFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method returns the correctly formatted log output.

        This test verifies that the formatted output matches the expected structure,
        including the log level name and the log message.

        Parameters:
        ----------
        colored_formatter : ColoredFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The formatted output starts with the expected log level and message.
        """
        expected_output = (
            f"{logging.getLevelName(debug_log_record.levelno)}: {debug_log_record.msg}"
        )
        formatted_output = colored_formatter.format(debug_log_record)

        # Directly comparing the output assuming it might include color codes
        assert formatted_output.startswith(
            f"DEBUG: Test message"
        ), f"Expected formatted output to start with '{expected_output}', but got '{formatted_output}'"
