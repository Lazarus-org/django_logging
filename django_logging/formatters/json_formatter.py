import ast
import json
import re
from logging import LogRecord
from typing import Any

from django_logging.formatters.base import BaseStructuredFormatter


class JSONFormatter(BaseStructuredFormatter):
    """A custom log formatter that formats log records as JSON strings, and
    converts 'key=value' patterns in the log message to key-value pairs in
    JSON.

    It also handles complex types such as lists, dicts, and tuples.

    """

    key_value_pattern = re.compile(
        r"(?P<key>\w+)=(?P<value>\{.*?\}|\[.*?\]|\(.*?\)|\S+)"
    )

    def format(self, record: LogRecord) -> str:
        """Formats the log record as a JSON string, and converts 'key=value'
        patterns in the log message to key-value pairs in JSON.

        Args:
        ----
            record (logging.LogRecord): The log record object.

        Returns:
        -------
            str: The formatted JSON string.

        """
        # Format the log data based on specifiers
        log_data = {
            specifier: self._handle_complex_value(
                self._get_field_value(record, specifier)
            )
            for specifier in self.specifiers
        }

        # Parse 'key=value' pairs from the message if present
        message = record.getMessage()
        key_value_pairs = self._extract_key_value_pairs(message)

        # If key-value pairs are extracted, update the log data and remove them from the message
        if key_value_pairs:
            log_data.update(key_value_pairs)
            message = self._remove_key_value_pairs(message)

        # Clean up the message: remove \n and \t
        message = self._clean_message(message)

        # Update the message field with the cleaned-up version
        log_data["message"] = message

        # Add any exception information if available
        self._add_exception(record, log_data)

        # Return the log data as a formatted JSON string
        return json.dumps(log_data, indent=2)

    def _extract_key_value_pairs(self, message: str) -> dict:
        """Extracts 'key=value' pairs from the log message and returns them as
        a dictionary. Supports complex structures like dict, list, and tuple.

        Args:
        ----
            message (str): The log message string.

        Returns:
        -------
            dict: A dictionary of extracted key-value pairs.

        """
        key_value_dict = {}
        for match in self.key_value_pattern.finditer(message):
            key = match.group("key")
            value = match.group("value")

            # Try to interpret the value as a dict, list, tuple, or other primitive types
            key_value_dict[key] = self._convert_value(value)

        return key_value_dict

    def _remove_key_value_pairs(self, message: str) -> str:
        """Removes key=value pairs from the log message string to avoid
        duplication.

        Args:
        ----
            message (str): The original log message string.

        Returns:
        -------
            str: The cleaned-up message string without key=value pairs.

        """
        # Replace the key=value pairs in the message with an empty string
        return self.key_value_pattern.sub("", message).strip()

    def _clean_message(self, message: str) -> str:
        """Cleans up the log message by removing any '\n' (newlines) and '\t'
        (tabs).

        Args:
        ----
            message (str): The log message string to clean.

        Returns:
        -------
            str: The cleaned message without newlines and tabs.

        """
        return message.replace("\n", " ").replace("\t", " ").strip()

    def _convert_value(self, value: str) -> Any:
        """Tries to convert a string value to an appropriate type (int, float,
        bool, dict, list, tuple). If conversion fails, returns the value as a
        string.

        Args:
        ----
            value (str): The string value to convert.

        Returns:
        -------
            any: The converted value.

        """
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        try:
            # Use ast.literal_eval to safely parse dict, list, or tuple from the string
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If it's not a valid literal, return the original string
            return value
