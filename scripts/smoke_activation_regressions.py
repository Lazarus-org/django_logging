"""Dependency-free regression checks for safe component activation.

No Django settings shim is necessary: the component compiler and
activator only use the Python logging module. This complements, but does
not replace, Django and multi-process integration tests.

"""

import importlib.util
import logging
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


components = load("dj_components_regression", "django_logging/settings/components.py")
activation = load("dj_activation_regression", "django_logging/settings/activation.py")


class UnusedHandler(logging.Handler):
    def __init__(self):
        raise AssertionError("An unattached handler should never be constructed")

    def emit(self, record):
        pass


class UnusedFilter(logging.Filter):
    def __init__(self):
        raise AssertionError("An unattached filter should never be constructed")


class UnusedFormatter(logging.Formatter):
    def __init__(self):
        raise AssertionError("An unattached formatter should never be constructed")


class CloseTrackingSink(logging.NullHandler):
    was_closed = False

    def close(self):
        self.was_closed = True
        super().close()


def base():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": "%(message)s"}},
        "filters": {},
        "handlers": {
            "built_in": {"class": "logging.NullHandler"},
            "console": {"class": "logging.StreamHandler"},
        },
        "loggers": {},
        "root": {"handlers": ["built_in", "console"], "level": "DEBUG"},
    }


def run():
    root = logging.getLogger()
    pkg = logging.getLogger("django_logging")
    before = {
        logger: (
            list(logger.handlers),
            list(logger.filters),
            logger.level,
            logger.propagate,
        )
        for logger in (root, pkg)
    }
    try:
        extensions = {
            "formatters": {"unused_formatter": {"()": UnusedFormatter}},
            "filters": {"unused_filter": {"()": UnusedFilter}},
            "handlers": {
                "unused": {
                    "()": UnusedHandler,
                    "formatter": "unused_formatter",
                    "filters": ["unused_filter"],
                },
                "buffer": {
                    "class": "logging.handlers.MemoryHandler",
                    "capacity": 4,
                    "target": "sink",
                },
                "sink": {"()": CloseTrackingSink},
            },
            "package_handlers": ["buffer"],
        }
        compiled = components.compile_components(base(), extensions)
        activation.activate(compiled, mode="isolated", resolver=lambda p: None)
        assert not any(h.name == "dj_logging:unused" for h in pkg.handlers)
        buffer = next(h for h in pkg.handlers if h.name == "dj_logging:buffer")
        assert isinstance(buffer, logging.handlers.MemoryHandler)
        assert isinstance(buffer.target, CloseTrackingSink)
        prior_sink = buffer.target

        # Explicit attachment of the otherwise suppressed console preset must
        # be honored, without adding two copies on repeated initialization.
        console = components.compile_components(base(), {"root_handlers": ["console"]})
        activation.activate(console, mode="additive", resolver=lambda p: None)
        assert (
            prior_sink.was_closed
        ), "unattached handler target leaked after reinitialization"
        assert len([h for h in root.handlers if h.name == "dj_logging:console"]) == 1
        activation.activate(console, mode="additive", resolver=lambda p: None)
        assert len([h for h in root.handlers if h.name == "dj_logging:console"]) == 1

        # When not explicitly requested, console stays off root, and the host's
        # original handler list remains intact after the last transition.
        activation.activate(
            components.compile_components(base(), {}),
            mode="isolated",
            resolver=lambda p: None,
        )
        assert not any(h.name == "dj_logging:console" for h in root.handlers)
        assert root.handlers == before[root][0]
        print("ACTIVATION_REGRESSION_SMOKE_PASS")
    finally:
        for logger, (handlers, filters, level, propagate) in before.items():
            for h in list(logger.handlers):
                if h not in handlers:
                    logger.removeHandler(h)
                    h.close()
            for handler in handlers:
                if handler not in logger.handlers:
                    logger.addHandler(handler)
            for flt in list(logger.filters):
                if flt not in filters:
                    logger.removeFilter(flt)
            for flt in filters:
                if flt not in logger.filters:
                    logger.addFilter(flt)
            logger.setLevel(level)
            logger.propagate = propagate
        activation._CONTROLLED.clear()
        activation._CONTROLLED_FILTERS.clear()
        activation._ACTIVE_HANDLERS = ()


if __name__ == "__main__":
    run()
