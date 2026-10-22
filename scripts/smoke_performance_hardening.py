"""Dependency-free smoke tests for performance/resource-bound changes."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from django_logging.contextvar.contextvar_manager import ContextVarManager  # noqa: E402
from django_logging.formatters.flat_formatter import FLATFormatter  # noqa: E402
from django_logging.formatters.json_formatter import JSONFormatter  # noqa: E402
from django_logging.formatters.xml_formatter import XMLFormatter  # noqa: E402


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


def run() -> None:
    # Context lookup must not scan or copy variables owned by unrelated libs.
    manager = ContextVarManager()
    manager.bind(request_id="req-1", tenant_id="tenant-1")
    unrelated = [contextvars.ContextVar(f"unrelated_{i}") for i in range(500)]
    for index, variable in enumerate(unrelated):
        variable.set(index)
    expected = {"request_id": "req-1", "tenant_id": "tenant-1"}
    assert manager.get_contextvars() == expected

    # The traversal must stop early even if a custom Mapping has huge branches.
    nested = CountingMapping({f"child_{index}": "x" * 1000 for index in range(1000)})
    root = CountingMapping({f"branch_{index}": nested for index in range(1000)})
    record = logging.LogRecord(
        "benchmark", logging.INFO, __file__, 1, "bounded message", (), None
    )
    record.payload = root
    formatter = JSONFormatter(
        "%(message)s",
        structured_logging={"MAX_EVENT_BYTES": 96, "MAX_ITEMS": 1000, "MAX_DEPTH": 32},
    )
    rendered = formatter.format(record)
    parsed = json.loads(rendered)
    assert len(rendered.encode("utf-8")) <= 96
    assert parsed["message"] == "bounded message"
    assert root.items_yielded < 10, root.items_yielded
    assert nested.items_yielded < 10, nested.items_yielded

    # All built-in structured formatters must remain bounded on hostile payloads.
    huge_message = "x" * 10_000_000
    for formatter_type in (JSONFormatter, FLATFormatter, XMLFormatter):
        large_record = logging.LogRecord(
            "benchmark", logging.INFO, __file__, 1, huge_message, (), None
        )
        bounded_formatter = formatter_type(
            "%(message)s", structured_logging={"MAX_EVENT_BYTES": 96}
        )
        output = bounded_formatter.format(large_record)
        assert len(output.encode("utf-8")) <= 96, formatter_type.__name__
        if formatter_type is JSONFormatter:
            assert json.loads(output)["message"] != "[log event omitted: too large]"
        elif formatter_type is XMLFormatter:
            ET.fromstring(output)
    print("PERFORMANCE_HARDENING_SMOKE_PASS")


if __name__ == "__main__":
    run()
