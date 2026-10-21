"""Boundary and regression tests for bounded structured serialization."""

import decimal
import json
import logging
import sys
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django_logging.constants.structured_validation import structured_logging_errors
from django_logging.formatters import (
    ColoredFormatter,
    FLATFormatter,
    JSONFormatter,
    XMLFormatter,
)
from django_logging.formatters.base import BaseStructuredFormatter


def event(**fields):
    return logging.makeLogRecord({"msg": "bounded", "args": (), **fields})


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        (True, True),
        (False, False),
        (0, 0),
        (1.25, 1.25),
        (float("inf"), None),
        (float("nan"), None),
        (decimal.Decimal("1.25"), "1.25"),
        (b"secret", "[binary omitted]"),
        ("é😀", "é😀"),
    ],
)
def test_scalar_values_keep_types_and_safe_representations(value, expected):
    formatter = BaseStructuredFormatter()
    assert formatter._handle_complex_value(value) == expected


def test_scalar_budgets_and_legacy_budget_shape():
    formatter = BaseStructuredFormatter()
    assert formatter._sanitize(1, budget=[1]) == 1
    assert formatter._sanitize("anything", budget=[0, 100]) == "[OMITTED]"
    assert formatter._sanitize(None, budget=[1, 6]) == "[OMITTED]"
    assert formatter._sanitize(True, budget=[1, 6]) == "[OMITTED]"
    assert formatter._sanitize(b"large binary", budget=[1, 6]) == "[OMITTED]"
    assert formatter._sanitize_text("text", [1, 0]) == "[OMITTED]"


def test_unicode_truncation_never_splits_a_codepoint():
    formatter = BaseStructuredFormatter()
    assert formatter._sanitize("éé", budget=[1, 18]) == "é"
    assert formatter._sanitize("😀", budget=[1, 6]) == "[OMITTED]"
    assert formatter._sanitize("\ud800") == "?"


def test_depth_items_keys_and_decimal_limits():
    formatter = BaseStructuredFormatter(structured_logging={"MAX_DEPTH": 1})
    assert formatter._sanitize({"nested": [1, 2]}) == {"nested": "[OMITTED]"}
    limited = BaseStructuredFormatter(structured_logging={"MAX_ITEMS": 1})
    assert limited._sanitize([1, 2]) == [1, "[OMITTED]"]
    assert formatter._sanitize({"[OMITTED]": "hidden"}) == {"_truncated": True}
    small = BaseStructuredFormatter(structured_logging={"MAX_STRING_LENGTH": 2})
    assert small._sanitize(decimal.Decimal("123")) == "[OMITTED]"
    assert formatter._sanitize(decimal.Decimal("123"), budget=[1, 6]) == "[OMITTED]"


@pytest.mark.parametrize("formatter_type", [JSONFormatter, FLATFormatter, XMLFormatter])
def test_large_integers_are_omitted_without_crashing(formatter_type):
    with patch.object(sys, "get_int_max_str_digits", return_value=4300, create=True):
        output = formatter_type("%(message)s").format(event(count=10**4500))
    assert "[OMITTED]" in output
    assert "bounded" in output


def test_python_without_integer_conversion_limit(monkeypatch):
    monkeypatch.delattr(sys, "get_int_max_str_digits", raising=False)
    assert BaseStructuredFormatter()._sanitize(12) == 12


@pytest.mark.parametrize("formatter_type", [JSONFormatter, FLATFormatter, XMLFormatter])
def test_final_size_check_returns_a_valid_small_envelope(formatter_type):
    key = "long_field_" * 30
    formatter = formatter_type(
        f"%({key})s %(message)s", structured_logging={"MAX_EVENT_BYTES": 96}
    )
    output = formatter.format(event(**{key: "x"}))
    assert len(output.encode("utf-8")) <= 96
    assert "log event omitted: too large" in output
    if formatter_type is JSONFormatter:
        assert json.loads(output)["message"]
    elif formatter_type is XMLFormatter:
        assert ET.fromstring(output).find("message") is not None


def test_flat_non_string_fields_and_extra_item_limit():
    output = FLATFormatter("%(lineno)s %(message)s").format(event(lineno=12))
    assert "lineno='12'" in output
    data = json.loads(
        JSONFormatter("%(message)s", structured_logging={"MAX_ITEMS": 1}).format(
            event(first=1, second=2)
        )
    )
    assert data["extra"]["first"] == 1
    assert data["extra"]["_truncated"] is True


def test_exception_budgets_and_legacy_xml_exception_helper():
    record = event(exc_info=(ValueError, ValueError("failure"), None))
    formatter = BaseStructuredFormatter(structured_logging={"MAX_STRING_LENGTH": 3})
    assert formatter._exception_value(record, budget=[0, 100]) == "[OMITTED]"
    with patch(
        "django_logging.formatters.base.traceback.TracebackException",
        return_value=SimpleNamespace(format=lambda: iter(["abc", "more"])),
    ):
        assert formatter._exception_value(record) == "abc"
    with patch(
        "django_logging.formatters.base.traceback.TracebackException",
        return_value=SimpleNamespace(format=lambda: iter(["abcdef"])),
    ):
        assert formatter._exception_value(record) == "abc"
    root = ET.Element("log")
    xml = XMLFormatter(structured_logging={"EXCEPTION_MODE": "type"})
    xml._add_exception_to_xml(record, root)
    assert root.find("exception").text == "ValueError"


def test_xml_pretty_print_rejects_declarations_and_large_input():
    formatter = XMLFormatter(structured_logging={"MAX_EVENT_BYTES": 96})
    assert "\n  <message>ok" in formatter._pretty_print_xml(
        "<log><message>ok</message></log>"
    )
    for value in (
        "<!DOCTYPE log><log/>",
        "<!ENTITY x 'secret'><log/>",
        "x" * 97,
        "é" * 49,
    ):
        with pytest.raises(ValueError):
            formatter._pretty_print_xml(value)


def test_default_colored_formatter_and_structured_schema_type():
    assert (
        ColoredFormatter("\x1b[31m%(message)s\x1b[0m").format(event())
        == "\x1b[31mbounded\x1b[0m"
    )
    assert "must be a dictionary" in structured_logging_errors([])[0]


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", ""),
        ("plain <tag> & text", "plain <tag> & text"),
        ("\t\n\r\x00\x08\x0b\x0c\x1f", "\t\n\r"),
        ("\ud7ff\ud800\udfff\ue000\ufffd\ufffe\uffff", "\ud7ff\ue000\ufffd"),
        ("سفارش 😀\U0010ffff", "سفارش 😀\U0010ffff"),
        (123, "123"),
    ],
)
def test_xml_text_preserves_xml_10_character_boundaries(value, expected):
    from django_logging.formatters.xml_formatter import _xml_text

    assert _xml_text(value) == expected
