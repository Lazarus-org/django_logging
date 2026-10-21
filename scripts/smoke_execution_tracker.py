"""Dependency-free regression smoke test for the execution tracker.

This deliberately stubs Django's settings/connection interface and the
validator imports. It exercises the production decorator implementation,
but does not replace the Django integration suite.

"""

import asyncio
import importlib.util
import logging
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def package(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module
    return module


package("django")
package("django.conf")
sys.modules["django.conf"].settings = types.SimpleNamespace(DEBUG=True)
package("django.db")
connection = types.SimpleNamespace(queries_log=[{"sql": "pre-existing", "time": "0"}])
sys.modules["django.db"].connection = connection
package("django_logging")
package("django_logging.utils")
package("django_logging.validators")
package("django_logging.decorators")
validator = types.ModuleType("django_logging.validators.config_validators")
validator.validate_boolean_setting = lambda value, name: (
    [] if isinstance(value, bool) else [name]
)
validator.validate_integer_setting = lambda value, name: (
    []
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0
    else [name]
)
sys.modules[validator.__name__] = validator

spec = importlib.util.spec_from_file_location(
    "django_logging.utils.time", ROOT / "django_logging/utils/time.py"
)
time_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = time_module
spec.loader.exec_module(time_module)

spec = importlib.util.spec_from_file_location(
    "django_logging.decorators.execution_tracking",
    ROOT / "django_logging/decorators/execution_tracking.py",
)
tracker_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tracker_module
spec.loader.exec_module(tracker_module)
execution_tracker = tracker_module.execution_tracker


@execution_tracker(log_queries=True, query_threshold=0, query_exceed_warning=True)
def sync_action():
    connection.queries_log.append({"sql": "SELECT 1", "time": "0"})
    return 100


async def check_async() -> None:
    started = asyncio.Event()
    proceed = asyncio.Event()

    @execution_tracker()
    async def action():
        started.set()
        await proceed.wait()
        return 200

    with patch.object(tracker_module.logger, "log") as emit:
        task = asyncio.create_task(action())
        await started.wait()
        assert emit.call_count == 0
        proceed.set()
        assert await task == 200
        assert emit.call_count == 1
        assert "Performance Metrics" in emit.call_args.args[1]

    try:

        @execution_tracker(log_queries=True)
        async def unsupported():
            return 1

    except ValueError as exc:
        assert "async" in str(exc)
    else:
        raise AssertionError("Async query counting must fail explicitly")


if __name__ == "__main__":
    original_level = tracker_module.logger.level
    tracker_module.logger.setLevel(logging.INFO)
    try:
        with (
            patch.object(tracker_module.logger, "log") as emit,
            patch.object(tracker_module.logger, "warning") as warn,
        ):
            assert sync_action() == 100
            assert connection.queries_log[0]["sql"] == "pre-existing"
            assert "Database Queries: 1 queries" in emit.call_args.args[1]
            assert warn.call_count == 1
        asyncio.run(check_async())
        tracker_module.logger.setLevel(logging.WARNING)
        with (
            patch.object(tracker_module.logger, "log") as emit,
            patch.object(tracker_module.logger, "warning") as warn,
        ):
            assert sync_action() == 100
            assert not emit.called
            assert warn.call_count == 1
    finally:
        tracker_module.logger.setLevel(original_level)
    print("Execution tracker smoke tests passed (Django imports stubbed)")
