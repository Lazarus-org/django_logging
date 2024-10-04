import logging
import sys

import pytest

from django_logging.formatters import FLATFormatter
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.formatters,
    pytest.mark.flat_formatter,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestFLATFormatter:

    def test_format_flat_record(
        self, flat_formatter: FLATFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method formats a log record into a single flat line.

        Args:
        ----
            flat_formatter (FLATFormatter): The formatter instance being tested.
            debug_log_record (logging.LogRecord): The dummy log record to format.

        Asserts:
        -------
            - The flat line contains key-value pairs for each specifier.
            - There is no 'None' or empty fields in the formatted log.
        """
        debug_log_record.custom_field = "custom_value"
        flat_formatter.specifiers = ["asctime", "levelname", "message", "custom_field"]

        formatted_output = flat_formatter.format(debug_log_record)

        # Check for presence of the fields as key-value pairs in the output
        assert "asctime" in formatted_output, "asctime field not present."
        assert (
            "levelname='DEBUG'" in formatted_output
        ), "levelname field incorrectly formatted."
        assert (
            "custom_field='custom_value'" in formatted_output
        ), "custom_field incorrectly formatted."
        assert "message" in formatted_output, "message field not present."

    def test_format_with_exception(
        self, flat_formatter: FLATFormatter, error_with_exc_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method correctly adds exception debugrmation to the flat line string.

        Args:
        ----
            flat_formatter (FLATFormatter): The formatter instance being tested.
            error_with_exc_log_record (logging.LogRecord): The dummy log record with an exception.

        Asserts:
        -------
            - The exception debug is included in the flat line.
        """
        flat_formatter.specifiers = ["asctime", "levelname", "message"]

        formatted_output = flat_formatter.format(error_with_exc_log_record)

        # Check that exception debug is included in the output
        assert "exception" in formatted_output, "Exception info not present in the formatted log."
