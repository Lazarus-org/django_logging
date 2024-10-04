import sys
from logging import LogRecord

import pytest

from django_logging.formatters.base import BaseStructuredFormatter
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.formatters,
    pytest.mark.base_formatter,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestBaseStructuredFormatter:

    def test_extract_specifiers(self) -> None:
        """
        Test that the `_extract_specifiers` method correctly extracts format specifiers from the provided format string.

        Asserts:
        -------
            - The extracted specifiers match the expected list.
        """
        fmt_string = "%(levelname)s | %(asctime)s | %(message)s | %(custom_field)s"
        formatter = BaseStructuredFormatter(fmt=fmt_string)

        expected_specifiers = ["levelname", "asctime", "message", "custom_field"]
        assert formatter.specifiers == expected_specifiers, (
            f"Expected specifiers {expected_specifiers}, "
            f"but got {formatter.specifiers}"
        )

    def test_extract_specifiers_empty_format(self) -> None:
        """
        Test that `_extract_specifiers` returns an empty list when no format string is provided.

        Asserts:
        -------
            - The specifiers list is empty.
        """
        formatter = BaseStructuredFormatter(fmt=None)
        assert (
            formatter.specifiers == []
        ), "Specifiers list should be empty when no format string is provided."

    def test_get_field_value(self, debug_log_record: LogRecord) -> None:
        """
        Test that `_get_field_value` correctly retrieves field values from the log record.

        Args:
        ----
            debug_log_record (logging.LogRecord): The log record instance with known fields.

        Asserts:
        -------
            - The `levelname` field value matches 'INFO'.
            - The `message` field value matches 'Test log message'.
            - The `custom_field` value matches 'CustomValue'.
        """
        fmt_string = "%(levelname)s | %(asctime)s | %(message)s | %(custom_field)s"
        formatter = BaseStructuredFormatter(fmt=fmt_string)

        # Test known fields from log record
        assert formatter._get_field_value(debug_log_record, "levelname") == "DEBUG"
        assert formatter._get_field_value(debug_log_record, "message") == "Test message"

        # Test custom field
        debug_log_record.custom_field = "CustomValue"
        assert formatter._get_field_value(debug_log_record, "custom_field") == "CustomValue"

    def test_get_field_value_unknown_field(self, error_with_exc_log_record: LogRecord) -> None:
        """
        Test that `_get_field_value` returns None when an unknown field is requested.

        Args:
        ----
            error_with_exc_log_record (logging.LogRecord): The log record instance with no such field.

        Asserts:
        -------
            - The method returns None for an unknown field.
        """
        fmt_string = "%(unknown_field)s"
        formatter = BaseStructuredFormatter(fmt=fmt_string)
        formatter._add_exception(error_with_exc_log_record, {})

        assert (
            formatter._get_field_value(error_with_exc_log_record, "unknown_field") is None
        ), "Should return None for unknown field."
