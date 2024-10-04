import logging
import sys
import xml.etree.ElementTree as ET

import pytest

from django_logging.formatters.xml_formatter import XMLFormatter
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.formatters,
    pytest.mark.xml_formatter,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestXMLFormatter:

    def test_format_creates_valid_xml(
            self, xml_formatter: XMLFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method produces a valid XML string.

        This test checks if the output from the formatter is valid XML
        and can be parsed without errors.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The formatted output can be parsed as valid XML.
        """
        formatted_output = xml_formatter.format(debug_log_record)
        try:
            ET.fromstring(formatted_output)
        except ET.ParseError as e:
            pytest.fail(f"Formatted output is not valid XML: {e}")

    def test_format_includes_message_field(
            self, xml_formatter: XMLFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method includes the 'message' field in the output.

        This test ensures that the log record's message field is present in the
        formatted XML string.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The formatted XML contains the 'message' element.
        """
        formatted_output = xml_formatter.format(debug_log_record)
        root = ET.fromstring(formatted_output)
        message_element = root.find("message")
        assert message_element is not None, "Message field not found in XML."
        assert message_element.text == debug_log_record.getMessage(), (
            f"Expected message to be '{debug_log_record.getMessage()}', but got '{message_element.text}'"
        )

    def test_format_pretty_prints_xml(
            self, xml_formatter: XMLFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method returns a pretty-printed XML string.

        This test ensures that the XML output is indented and well-formatted.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture.

        Asserts:
        -------
        - The XML string is properly indented and formatted.
        """
        formatted_output = xml_formatter.format(debug_log_record)
        lines = formatted_output.split("\n")

        # Ensure there are multiple lines due to pretty-printing
        assert len(lines) > 1, "XML output is not pretty-printed."

        # Check indentation in the XML (default indent is 2 spaces)
        for line in lines[1:3]:
            if line.strip():
                assert line.startswith("  "), "XML elements are not properly indented."

    def test_format_includes_exception_if_present(
            self, xml_formatter: XMLFormatter, error_with_exc_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method includes the 'exception' field in the XML output
        if exception debug is present in the log record.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        error_log_record : logging.LogRecord
            A log record with an exception set in exc_debug.

        Asserts:
        -------
        - The XML output contains an 'exception' element when an exception is logged.
        """
        formatted_output = xml_formatter.format(error_with_exc_log_record)
        root = ET.fromstring(formatted_output)
        exception_element = root.find("exception")
        assert exception_element is not None, "Exception field not found in XML."
        assert exception_element.text, "Exception field is empty."

    def test_format_handles_list_in_field(
            self, xml_formatter: XMLFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method correctly handles a log field containing a list.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture, modified to include a list in a custom field.

        Asserts:
        -------
        - The XML output includes properly formatted list elements in the specified field.
        """
        # Modify the log record to include a list in a custom field
        debug_log_record.args = None  # Make sure it's not interfering
        debug_log_record.custom_list = [1, 2, 3, 4]
        xml_formatter.specifiers = ["custom_list"]

        formatted_output = xml_formatter.format(debug_log_record)
        root = ET.fromstring(formatted_output)

        # Check if the 'custom_list' field is correctly formatted as XML
        custom_list_element = root.find("custom_list")
        assert custom_list_element is not None, "custom_list field not found in XML."
        assert len(custom_list_element) == 4, "List items not correctly formatted in XML."
        for i, item in enumerate(custom_list_element):
            assert item.text == str(i + 1), f"List item {i} does not match expected value."

    def test_format_handles_dict_in_field(
            self, xml_formatter: XMLFormatter, debug_log_record: logging.LogRecord
    ) -> None:
        """
        Test that the `format` method correctly handles a log field containing a dictionary.

        Parameters:
        ----------
        xml_formatter : XMLFormatter
            The formatter instance being tested.
        debug_log_record : logging.LogRecord
            The dummy log record created by the fixture, modified to include a dict in a custom field.

        Asserts:
        -------
        - The XML output includes properly formatted dictionary elements in the specified field.
        """
        # Modify the log record to include a dict in a custom field
        debug_log_record.args = None  # Make sure it's not interfering
        debug_log_record.custom_dict = {"id": 123, "name": "John"}
        xml_formatter.specifiers = ["custom_dict"]

        formatted_output = xml_formatter.format(debug_log_record)
        root = ET.fromstring(formatted_output)

        # Check if the 'custom_dict' field is correctly formatted as XML
        custom_dict_element = root.find("custom_dict")
        assert custom_dict_element is not None, "custom_dict field not found in XML."

        # Verify that dictionary keys are formatted as child elements
        user_id_element = custom_dict_element.find("id")
        user_name_element = custom_dict_element.find("name")

        assert user_id_element is not None, "ID element not found in XML."
        assert user_name_element is not None, "Name element not found in XML."

        # Ensure that the values match
        assert user_id_element.text == "123", f"Expected ID to be '123', got {user_id_element.text}"
        assert user_name_element.text == "John", f"Expected name to be 'John', got {user_name_element.text}"
