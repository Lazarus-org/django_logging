"""Dependency-free tests for the public formatter and structured settings API."""

import json
import logging
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pytest

from django_logging.constants.structured_validation import (
    resolve_structured_logging,
    structured_logging_errors,
)
from django_logging.formatters.base import BaseStructuredFormatter
from django_logging.formatters.flat_formatter import FLATFormatter
from django_logging.formatters.json_formatter import JSONFormatter
from django_logging.formatters.xml_formatter import XMLFormatter


def record(message="hello", **extra):
    item = logging.LogRecord("app.test", logging.INFO, __file__, 10, message, (), None)
    item.context = extra.pop("context", {})
    item.__dict__.update(extra)
    return item


def test_json_single_line_and_original_message():
    msg = "service=login value=a\nb token=secret"
    output = JSONFormatter("%(levelname)s %(context)s %(message)s").format(record(msg))
    assert "\n" not in output
    assert json.loads(output)["message"] == msg
    assert "service" not in json.loads(output)


def test_typed_extra_and_recursive_redaction():
    obj = record(
        "plain",
        context={"request_id": "abc", "api_key": "never"},
        extra_info={"phone": "123", "count": 4, "nested": [{"password": "hide"}]},
        created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    parsed = json.loads(JSONFormatter("%(context)s %(message)s").format(obj))
    assert parsed["context"]["api_key"] == "[REDACTED]"
    assert parsed["context"]["request_id"] == "abc"
    assert parsed["extra"]["extra_info"] == {
        "phone": "[REDACTED]",
        "count": 4,
        "nested": [{"password": "[REDACTED]"}],
    }
    assert parsed["extra"]["created_at"] == "2026-01-02T00:00:00+00:00"


def test_xml_invalid_names_control_chars_and_escaping():
    obj = record("a<&\x00b", context={"bad key<": "a&b", "token": "never"})
    output = XMLFormatter("%(context)s %(message)s").format(obj)
    root = ET.fromstring(output)
    assert root.find("message").text == "a<&b"
    assert root.find("context/field[@name='bad key<']").text == "a&b"
    assert root.find("context/token").text == "[REDACTED]"


def test_flat_single_line_escaped_value():
    obj = record("line1\nline2 ' quoted")
    output = FLATFormatter("%(levelname)s %(message)s").format(obj)
    assert "\n" not in output
    assert r"\n" in output
    assert "\\'" in output
    assert "levelname='INFO'" in output


def test_unsupported_objects_and_cycle_are_bounded():
    class Secret:
        def __str__(self):
            raise AssertionError("arbitrary object's __str__ must not run")

    cyclic = []
    cyclic.append(cyclic)
    obj = record("normal", payload={"object": Secret(), "cycle": cyclic})
    parsed = json.loads(JSONFormatter("%(message)s").format(obj))
    assert parsed["extra"]["payload"]["object"] == "[unsupported object]"
    assert parsed["extra"]["payload"]["cycle"] == ["[circular]"]


def test_limits_apply_to_fields_and_total_size():
    cfg = {"MAX_STRING_LENGTH": 50, "MAX_EVENT_BYTES": 96, "MAX_DEPTH": 2}
    fmt = JSONFormatter("%(message)s", structured_logging=cfg)
    parsed = json.loads(fmt.format(record("x" * 300)))
    assert len(parsed["message"]) <= 50
    assert "omitted" not in parsed["message"]
    rendered = fmt.format(record("y", detail={"very_long": "z" * 200}))
    parsed = json.loads(rendered)
    assert len(rendered.encode("utf-8")) <= 96
    assert parsed["message"] == "y"
    assert "[OMITTED]" in rendered


def test_exception_policy_and_record_remains_unmodified():
    try:
        raise RuntimeError("secret potentially present")
    except RuntimeError:
        ex = sys.exc_info()
    obj = record("something")
    obj.exc_info = ex
    typ = json.loads(
        JSONFormatter(
            "%(message)s", structured_logging={"EXCEPTION_MODE": "type"}
        ).format(obj)
    )
    assert typ["exception"] == "RuntimeError"
    omit = json.loads(
        JSONFormatter(
            "%(message)s", structured_logging={"EXCEPTION_MODE": "omit"}
        ).format(obj)
    )
    assert "exception" not in omit
    assert obj.exc_info == ex
    assert (
        "RuntimeError"
        in json.loads(JSONFormatter("%(message)s").format(obj))["exception"]
    )


def test_extra_cannot_override_reserved_fields():
    obj = record("true original", message2="different", event="login")
    data = json.loads(JSONFormatter("%(message)s").format(obj))
    assert data["message"] == "true original"
    assert data["extra"]["event"] == "login"


def test_custom_sensitive_fields():
    fmt = JSONFormatter(
        "%(context)s", structured_logging={"REDACT_FIELDS": ["private.identifier"]}
    )
    obj = record("hi", context={"private.identifier": "raw", "count": 1})
    parsed = json.loads(fmt.format(obj))
    assert parsed["context"] == {"private.identifier": "[REDACTED]", "count": 1}


@pytest.mark.parametrize(
    "bad",
    [
        {"MAX_DEPTH": True},
        {"MAX_EVENT_BYTES": 2},
        {"JSON_COMPACT": "yes"},
        {"EXCEPTION_MODE": "full"},
        {"REDACT_FIELDS": "password"},
        {"UNKNOWN": True},
    ],
)
def test_invalid_options_fail_before_use(bad):
    assert structured_logging_errors(bad)
    with pytest.raises(ValueError):
        resolve_structured_logging(bad)
    with pytest.raises(ValueError):
        BaseStructuredFormatter(structured_logging=bad)


def test_pretty_json_opt_in():
    fmt = JSONFormatter("%(message)s", structured_logging={"JSON_COMPACT": False})
    assert "\n" in fmt.format(record("one"))


def test_xml_message_is_bounded_before_serialization():
    fmt = XMLFormatter("%(message)s", structured_logging={"MAX_EVENT_BYTES": 96})
    rendered = fmt.format(record("z" * 500))
    root = ET.fromstring(rendered)
    assert root.find("message").text == "z" * 16
    assert len(rendered.encode("utf-8")) <= 96


def test_colored_formatter_does_not_mutate_template():
    from django_logging.formatters import ColoredFormatter

    formatter = ColoredFormatter("%(levelname)s %(message)s")
    for level in (logging.WARNING, logging.DEBUG, logging.INFO, logging.WARNING):
        item = record("hello")
        item.levelno = level
        item.levelname = logging.getLevelName(level)
        result = formatter.format(item)
        assert "hello" in result
        assert formatter._style._fmt == "%(levelname)s %(message)s"


def test_total_node_budget_stops_many_branching_values():
    payload = {f"item_{i}": {f"child_{j}": j for j in range(30)} for i in range(30)}
    fmt = JSONFormatter(
        "%(message)s", structured_logging={"MAX_ITEMS": 30, "MAX_DEPTH": 3}
    )
    obj = record("bounded", payload=payload)
    result = json.loads(fmt.format(obj))
    # Large nested data cannot require unbounded processing; output stays valid.
    assert result["message"] == "bounded"
    assert "extra" in result


def test_nested_mapping_iteration_stops_when_global_budget_is_exhausted():
    from collections.abc import Mapping

    class CountingMapping(Mapping):
        def __init__(self, data):
            self.data = data
            self.items_yielded = 0

        def __getitem__(self, key):
            return self.data[key]

        def __iter__(self):
            return iter(self.data)

        def __len__(self):
            return len(self.data)

        def items(self):
            for key, value in self.data.items():
                self.items_yielded += 1
                yield key, value

    nested = CountingMapping({f"child_{index}": "x" * 1000 for index in range(1000)})
    root = CountingMapping({f"branch_{index}": nested for index in range(1000)})
    formatter = JSONFormatter(
        "%(message)s",
        structured_logging={"MAX_EVENT_BYTES": 96, "MAX_ITEMS": 1000, "MAX_DEPTH": 32},
    )
    rendered = formatter.format(record("bounded", payload=root))
    parsed = json.loads(rendered)
    assert len(rendered.encode("utf-8")) <= 96
    assert root.items_yielded < 10
    assert nested.items_yielded < 10
    assert parsed["message"] == "bounded"


@pytest.mark.parametrize(
    "bad",
    [
        {"MAX_DEPTH": 33},
        {"MAX_ITEMS": 1001},
        {"MAX_STRING_LENGTH": 1_048_577},
        {"MAX_EVENT_BYTES": 1_048_577},
        {"MAX_EXCEPTION_FRAMES": 129},
        {"REDACT_FIELDS": ["x" * 257]},
    ],
)
def test_structured_limits_have_hard_upper_bounds(bad):
    with pytest.raises(ValueError):
        resolve_structured_logging(bad)


def test_very_long_field_names_are_bounded_and_values_redacted():
    long_key = "x" * 300 + "api-key"
    obj = record("bounded", payload={long_key: "do-not-leak"})
    rendered = JSONFormatter("%(message)s").format(obj)
    parsed = json.loads(rendered)
    payload = parsed.get("extra", {}).get("payload", {})
    assert "do-not-leak" not in rendered
    assert payload
    assert next(iter(payload.values())) == "[REDACTED]"


def test_traceback_frame_formatting_is_bounded():
    def recurse(depth):
        if depth:
            return recurse(depth - 1)
        raise RuntimeError("bounded failure")

    try:
        recurse(12)
    except RuntimeError:
        exc = sys.exc_info()
    obj = record("operation failed")
    obj.exc_info = exc
    rendered = JSONFormatter(
        "%(message)s",
        structured_logging={"MAX_EXCEPTION_FRAMES": 2},
    ).format(obj)
    parsed = json.loads(rendered)
    assert parsed["exception"].count('File "') <= 2
    assert len(rendered.encode("utf-8")) <= 65536
