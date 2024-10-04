import json
import logging
import sys

import pytest

from django_logging.formatters.json_formatter import JSONFormatter
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.formatters,
    pytest.mark.json_formatter,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestJSONFormatter:

    def test_format_creates_valid_json(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method produces a valid JSON string.

        This test checks whether the formatter's output is valid JSON
        and can be parsed into a Python dictionary.

        Parameters:
        ----------
        json_formatter : JSONFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The formatted output can be parsed as valid JSON.
        """
        formatted_output = json_formatter.format(debug_log_record)
        try:
            parsed_output = json.loads(formatted_output)
            assert isinstance(
                parsed_output, dict
            ), "Formatted output is not a valid JSON object."
        except json.JSONDecodeError as e:
            pytest.fail(f"Formatted output is not valid JSON: {e}")

    def test_format_includes_message(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method includes the 'message' field in the output.

        This test ensures that the log record's message is present in the formatted JSON string.

        Parameters:
        ----------
        json_formatter : JSONFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The 'message' field in the formatted output matches the log record's message.
        """
        formatted_output = json_formatter.format(debug_log_record)
        parsed_output = json.loads(formatted_output)
        assert (
            parsed_output["message"] == debug_log_record.getMessage()
        ), "Message field is missing or incorrect."

    def test_key_value_pairs_are_extracted(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method extracts 'key=value' pairs from the log message.

        This test checks that key-value pairs present in the log message are extracted and included in the JSON output.

        Parameters:
        ----------
        json_formatter : JSONFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture, which includes key-value pairs.

        Asserts:
        -------
        - The key-value pairs from the log message are correctly parsed and included in the JSON output.
        """
        debug_log_record.msg = "user_id=123 action=login is_active=True"
        formatted_output = json_formatter.format(debug_log_record)
        parsed_output = json.loads(formatted_output)

        assert parsed_output["user_id"] == 123, "Key 'user_id' not correctly extracted."
        assert (
            parsed_output["action"] == "login"
        ), "Key 'action' not correctly extracted."

    def test_clean_message_removes_key_value_pairs(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method removes key-value pairs from the message after extracting them.

        This test ensures that after key-value pairs are extracted, the original log message is cleaned up by removing those pairs.

        Parameters:
        ----------
        json_formatter : JSONFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture, which includes key-value pairs.

        Asserts:
        -------
        - The final message in the output does not include key-value pairs.
        """
        debug_log_record.msg = "user_id=123 action=login"
        formatted_output = json_formatter.format(debug_log_record)
        parsed_output = json.loads(formatted_output)

        # The message field should not include the key-value pairs
        assert parsed_output["message"] == "", "Message still contains key-value pairs."

    def test_format_handles_complex_types(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method correctly handles complex types such as dict, list, and tuple in the message.

        This test verifies that key-value pairs with complex types like dictionaries, lists, and tuples
        are parsed correctly and included in the JSON output.

        Parameters:
        ----------
        json_formatter : JSONFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture, which includes complex types.

        Asserts:
        -------
        - Complex types are correctly parsed and converted in the JSON output.
        """
        debug_log_record.msg = "data={'key': 'value'} items=[1,2,3] coords=(1,2)"
        formatted_output = json_formatter.format(debug_log_record)
        parsed_output = json.loads(formatted_output)

        assert parsed_output["data"] == {
            "key": "value"
        }, "Dictionary type not correctly parsed."
        assert parsed_output["items"] == [1, 2, 3], "List type not correctly parsed."
