"""Standalone standard-library smoke harness (does not require Django)."""

import importlib.util
import logging
import os
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "django_logging/settings"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, BASE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


c = load("extensions_check", "components.py")
a = load("activation_check", "activation.py")


def presets():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "%(message)s"}},
        "filters": {},
        "handlers": {
            "preset": {
                "class": "logging.NullHandler",
                "level": "INFO",
                "formatter": "simple",
            }
        },
        "loggers": {},
        "root": {"level": "DEBUG", "handlers": ["preset"]},
    }


root = logging.getLogger()
root_handlers = list(root.handlers)
old_root_level = root.level
pkg = logging.getLogger("django_logging")
pkg_handlers = list(pkg.handlers)
pkg_level = pkg.level
pkg_prop = pkg.propagate
sample = logging.getLogger("custom.audit")
before = (list(sample.handlers), sample.level, sample.propagate)
try:
    (Path(tempfile.gettempdir()) / "dj-logging-component-smoke.log").unlink(
        missing_ok=True
    )
    ext = {
        "formatters": {"audit_fmt": {"format": "%(message)s|%(levelname)s"}},
        "handlers": {
            "audit": {
                "class": "logging.FileHandler",
                "filename": str(
                    Path(tempfile.gettempdir()) / "dj-logging-component-smoke.log"
                ),
                "formatter": "audit_fmt",
            }
        },
        "loggers": {
            "custom.audit": {
                "handlers": ["audit"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
        "root_handlers": [],
    }
    mapping = c.compile_components(presets(), ext)
    a.activate(
        mapping, mode="additive", resolver=lambda path: a.logging.config._resolve(path)
    )
    assert sample.level == logging.DEBUG and sample.propagate is False
    sample.info("AUDIT RECORD")
    assert "AUDIT RECORD" in Path(ext["handlers"]["audit"]["filename"]).read_text()
    assert (
        root.level == old_root_level
        and root_handlers == root.handlers[: len(root_handlers)]
    )
    a.activate(
        mapping, mode="additive", resolver=lambda path: a.logging.config._resolve(path)
    )
    sample.info("ONCE ONLY")
    assert (
        Path(ext["handlers"]["audit"]["filename"]).read_text().count("ONCE ONLY") == 1
    )
    # Explicit override + disable preset.
    updated = c.compile_components(
        presets(),
        {
            "disable": {"handlers": ["preset"]},
            "handlers": {"sink": {"class": "logging.NullHandler"}},
            "loggers": {"custom.audit": {"handlers": ["sink"], "propagate": False}},
        },
    )
    a.activate(
        updated, mode="isolated", resolver=lambda path: a.logging.config._resolve(path)
    )
    assert not any(h.name == "dj_logging:audit" for h in sample.handlers)
    a.activate(
        c.compile_components(presets(), {}),
        mode="isolated",
        resolver=lambda path: a.logging.config._resolve(path),
    )
    assert sample.level == before[1] and sample.propagate == before[2]
    for bad in [
        {"handlers": {"preset": {"class": "logging.NullHandler"}}},
        {
            "handlers": {
                "unknown": {"class": "logging.NullHandler", "formatter": "missing"}
            }
        },
        {"root_handlers": ["missing"]},
        {"disable": {"filters": ["missing"]}},
    ]:
        try:
            c.compile_components(presets(), bad)
        except c.ComponentConfigurationError:
            pass
        else:
            raise AssertionError(f"Expected to reject {bad}")
    print("STDLIB_COMPONENT_SMOKE_PASS")
finally:
    for owner, initial in (
        (root, root_handlers),
        (pkg, pkg_handlers),
        (sample, before[0]),
    ):
        for handler in list(owner.handlers):
            if handler not in initial:
                owner.removeHandler(handler)
                handler.close()
        for handler in initial:
            if handler not in owner.handlers:
                owner.addHandler(handler)
    root.setLevel(old_root_level)
    pkg.setLevel(pkg_level)
    pkg.propagate = pkg_prop
    sample.setLevel(before[1])
    sample.propagate = before[2]
