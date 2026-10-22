"""Reproducible microbenchmarks for dj-logging's Python hot paths.

Run from the repository root:
    python scripts/benchmark_performance.py --iterations 10000

These are microbenchmarks, not substitutes for a real Django/Gunicorn load test.
The script deliberately reports the Python version and payload sizes so results
from different machines are not mistaken for directly comparable measurements.

"""

from __future__ import annotations

import argparse
import contextvars
import json
import logging
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from django_logging.contextvar.contextvar_manager import ContextVarManager
from django_logging.formatters.flat_formatter import FLATFormatter
from django_logging.formatters.json_formatter import JSONFormatter
from django_logging.formatters.xml_formatter import XMLFormatter, _xml_text


def measure(
    label, operation, *, iterations: int, repeats: int = 5
) -> dict[str, object]:
    operation()  # warm up imports, caches, and formatter state
    samples = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        for _ in range(iterations):
            operation()
        elapsed = time.perf_counter_ns() - started
        samples.append(elapsed / iterations)
    return {
        "name": label,
        "median_us_per_operation": round(statistics.median(samples) / 1000, 3),
        "iterations_per_repeat": iterations,
        "repeats": repeats,
    }


def legacy_context_lookup(manager: ContextVarManager) -> dict[str, object]:
    """Reproduce the pre-optimization whole-context scan for comparison."""
    result = {}
    context = contextvars.copy_context()
    prefix = manager.DJANGO_LOGGING_PREFIX
    for var in context:
        if var.name.startswith(prefix) and context[var] is not Ellipsis:
            result[var.name[len(prefix) :]] = context[var]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.iterations < 1 or args.repeats < 1:
        parser.error("--iterations and --repeats must be positive")

    results = []
    manager = ContextVarManager()
    manager.bind(request_id="req-123", tenant_id="tenant-42", user_id=17)
    assert manager.get_contextvars() == legacy_context_lookup(manager)
    results.append(
        measure(
            "context_lookup.optimized.no_unrelated_vars",
            manager.get_contextvars,
            iterations=args.iterations,
            repeats=args.repeats,
        )
    )
    results.append(
        measure(
            "context_lookup.legacy.no_unrelated_vars",
            lambda: legacy_context_lookup(manager),
            iterations=args.iterations,
            repeats=args.repeats,
        )
    )

    unrelated = []
    for index in range(100):
        var = contextvars.ContextVar(f"benchmark_unrelated_{index}", default=None)
        var.set(index)
        unrelated.append(var)
    assert manager.get_contextvars() == legacy_context_lookup(manager)
    results.append(
        measure(
            "context_lookup.optimized.100_unrelated_vars",
            manager.get_contextvars,
            iterations=args.iterations,
            repeats=args.repeats,
        )
    )
    results.append(
        measure(
            "context_lookup.legacy.100_unrelated_vars",
            lambda: legacy_context_lookup(manager),
            iterations=args.iterations,
            repeats=args.repeats,
        )
    )

    record = logging.LogRecord(
        "dj_logging.benchmark",
        logging.INFO,
        __file__,
        1,
        "request completed",
        (),
        None,
    )
    record.context = {"request_id": "req-123", "tenant_id": "tenant-42"}
    record.created_at = datetime.now(timezone.utc)
    record.payload = {
        "operation": "list_orders",
        "items": [{"id": index, "status": "delivered"} for index in range(20)],
    }
    for formatter_cls in (JSONFormatter, FLATFormatter, XMLFormatter):
        formatter = formatter_cls("%(levelname)s %(context)s %(message)s")
        results.append(
            measure(
                f"formatter.{formatter_cls.__name__}.nested_extra",
                lambda formatter=formatter: formatter.format(record),
                iterations=max(100, args.iterations // 10),
                repeats=args.repeats,
            )
        )

    json_without_extra = JSONFormatter(
        "%(levelname)s %(context)s %(message)s",
        structured_logging={"INCLUDE_EXTRA": False},
    )
    results.append(
        measure(
            "formatter.JSONFormatter.nested_extra_disabled",
            lambda: json_without_extra.format(record),
            iterations=max(100, args.iterations // 10),
            repeats=args.repeats,
        )
    )

    try:
        from django.conf import settings

        if not settings.configured:
            settings.configure(DJANGO_LOGGING={"AUTO_INITIALIZATION_ENABLE": False})
        from django_logging.decorators.execution_tracking import execution_tracker
        from django_logging.decorators.execution_tracking import (
            logger as tracker_logger,
        )
        from django_logging.middleware.request_middleware import RequestLogMiddleware
    except (ImportError, ModuleNotFoundError):
        path_benchmark = "skipped (Django/asgiref not installed)"
    else:
        path = "/api/v1/orders/" + "a" * 180
        results.append(
            measure(
                "middleware.safe_path.printable_200_chars",
                lambda: RequestLogMiddleware._safe_path(path),
                iterations=args.iterations,
                repeats=args.repeats,
            )
        )
        path_benchmark = "included"
        original_level, original_propagate = (
            tracker_logger.level,
            tracker_logger.propagate,
        )
        silent = logging.NullHandler()
        tracker_logger.addHandler(silent)
        tracker_logger.propagate = False
        try:
            tracked = execution_tracker()(lambda: 42)
            for name, level in (
                ("disabled", logging.WARNING),
                ("enabled", logging.INFO),
            ):
                tracker_logger.setLevel(level)
                results.append(
                    measure(
                        f"execution_tracker.metrics_{name}",
                        tracked,
                        iterations=args.iterations,
                        repeats=args.repeats,
                    )
                )
        finally:
            tracker_logger.removeHandler(silent)
            tracker_logger.setLevel(original_level)
            tracker_logger.propagate = original_propagate

    for name, text in (
        ("ascii", "request completed " * 12),
        ("unicode", "سفارش ثبت شد 😀 " * 12),
    ):
        results.append(
            measure(
                f"xml_text.{name}",
                lambda text=text: _xml_text(text),
                iterations=args.iterations,
                repeats=args.repeats,
            )
        )

    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "path_benchmark": path_benchmark,
                "results": results,
                "note": "Microbenchmarks only; run Django/Gunicorn load tests for end-to-end conclusions.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
