import xml.etree.ElementTree as ET  # nosec B405
from logging import LogRecord
from typing import Any
from xml.dom import minidom  # nosec B408

from django_logging.formatters.base import (  # pylint: disable=E0401, E0611
    BaseStructuredFormatter,
)


class XMLFormatter(BaseStructuredFormatter):
    """A custom log formatter that formats log records as XML strings."""

    def format(self, record: LogRecord) -> str:
        """Converts the log record to an XML string.

        Args:
        ----
            record (logging.LogRecord): The log record object.

        Returns:
        -------
            str: The formatted XML string.

        """
        log_element = ET.Element("log")
        for specifier in self.specifiers:
            value = self._get_field_value(record, specifier)
            if value not in [None, ""]:
                self._add_field_to_xml(
                    log_element, specifier, self._handle_complex_value(value)
                )

        self._add_exception_to_xml(record, log_element)
        return self._pretty_print_xml(ET.tostring(log_element, encoding="unicode"))

    def _add_field_to_xml(
        self, parent_element: ET.Element, field_name: str, field_value: Any
    ) -> None:
        """Adds a field and its value to the XML structure.

        Args:
        ----
            parent_element (ET.Element): The parent XML element.
            field_name (str): The name of the field.
            field_value (Any): The value of the field.

        """
        field_element = ET.SubElement(parent_element, field_name)
        if isinstance(field_value, dict):
            for sub_key, sub_value in field_value.items():
                sub_element = ET.SubElement(field_element, sub_key)
                sub_element.text = str(sub_value)

        elif isinstance(field_value, (list, tuple)):
            for index, item in enumerate(field_value):
                sub_element = ET.SubElement(field_element, f"item_{index}")
                sub_element.text = str(item)
        else:
            field_element.text = str(field_value)

    def _add_exception_to_xml(
        self, record: LogRecord, parent_element: ET.Element
    ) -> None:
        """Adds exception information to the XML structure, if present in the
        log record.

        Args:
        ----
            record (logging.LogRecord): The log record object.
            parent_element (ET.Element): The parent XML element to which exception info will be added.

        """
        if record.exc_info:
            exception_element = ET.SubElement(parent_element, "exception")
            exception_element.text = self.formatException(record.exc_info)

    def _pretty_print_xml(self, xml_string: str) -> str:
        """Pretty-prints the XML string.

        Args:
        ----
            xml_string (str): The raw XML string.

        Returns:
        -------
            str: The pretty-printed XML string.

        """
        dom = minidom.parseString(xml_string)  # nosec B318
        return dom.toprettyxml(indent="  ", newl="\n").split("?>", 1)[-1].strip()
