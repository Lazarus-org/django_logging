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

    def test_message_key_values_are_not_reinterpreted(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        debug_log_record.msg = "user_id=123 action=login password=private"
        parsed = json.loads(json_formatter.format(debug_log_record))
        assert parsed["message"] == debug_log_record.msg
        assert "password" not in parsed
        assert "user_id" not in parsed

    def test_extra_fields_are_typed_and_redacted(
        self, json_formatter: JSONFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        debug_log_record.context = {"request_id": "test", "access_token": "secret"}
        debug_log_record.custom_dict = {"id": 123, "secret": "value"}
        debug_log_record.custom_list = [1, 2, 3]
        json_formatter.specifiers = ["context", "levelname"]
        parsed = json.loads(json_formatter.format(debug_log_record))
        assert parsed["context"] == {"request_id": "test", "access_token": "[REDACTED]"}
        assert parsed["extra"]["custom_dict"] == {"id": 123, "secret": "[REDACTED]"}
        assert parsed["extra"]["custom_list"] == [1, 2, 3]
