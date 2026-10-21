"""XML formatter with safe names, bounded values and valid XML characters."""

import re
import xml.etree.ElementTree as ET  # nosec B405: parsing below rejects DTD/entity declarations.
from logging import LogRecord
from typing import Any

from django_logging.formatters.base import BaseStructuredFormatter

_TAG = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
_INVALID_XML_TEXT = re.compile(
    r"[^\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]"
)


def _xml_text(value: Any) -> str:
    # XML 1.0 forbids C0 controls except tab/newline/carriage return and
    # surrogate code points. Escaping alone cannot make these valid.
    return _INVALID_XML_TEXT.sub("", str(value))


class XMLFormatter(BaseStructuredFormatter):
    """Existing pretty XML presentation with safe nested field handling."""

    def format(self, record: LogRecord) -> str:
        root = ET.Element("log")
        for key, value in self._event(record).items():
            self._add_field_to_xml(root, key, value)
        if self.options["XML_PRETTY"]:
            ET.indent(root, space="  ")
        result = ET.tostring(root, encoding="unicode")
        if len(result.encode("utf-8")) > self.options["MAX_EVENT_BYTES"]:
            return "<log><message>[log event omitted: too large]</message></log>"
        return result

    def _add_field_to_xml(
        self, parent_element: ET.Element, field_name: str, field_value: Any
    ) -> None:
        if _TAG.fullmatch(field_name) and not field_name.casefold().startswith("xml"):
            element = ET.SubElement(parent_element, field_name)
        else:
            element = ET.SubElement(
                parent_element, "field", {"name": _xml_text(field_name)}
            )
        if isinstance(field_value, dict):
            for key, value in field_value.items():
                self._add_field_to_xml(element, key, value)
        elif isinstance(field_value, list):
            for index, value in enumerate(field_value):
                self._add_field_to_xml(element, f"item_{index}", value)
        elif field_value is not None:
            element.text = _xml_text(field_value)

    def _add_exception_to_xml(
        self, record: LogRecord, parent_element: ET.Element
    ) -> None:
        exception = self._exception_value(record)
        if exception is not None:
            self._add_field_to_xml(parent_element, "exception", exception)

    def _pretty_print_xml(self, xml_string: str) -> str:
        """Retain public utility method for existing callers."""
        if (
            len(xml_string) > self.options["MAX_EVENT_BYTES"]
            or len(xml_string.encode("utf-8")) > self.options["MAX_EVENT_BYTES"]
        ):
            raise ValueError("XML exceeds MAX_EVENT_BYTES")
        if "<!DOCTYPE" in xml_string.upper() or "<!ENTITY" in xml_string.upper():
            raise ValueError("XML declarations are not supported")
        root = ET.fromstring(
            xml_string
        )  # nosec B314: bounded input, DTD and entities rejected above.
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")
