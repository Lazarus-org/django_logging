"""Checkpoint 06: generic and explicit extensions to automatic logging presets."""

import logging
import logging.handlers

import pytest
from django.test import override_settings

from django_logging.settings.checks import check_logging_components
from django_logging.settings.components import (
    ComponentConfigurationError,
    compile_components,
)
from django_logging.settings.conf import LogConfig, LogManager


class AuditFormatter(logging.Formatter):
    def format(self, record):
        return f"AUDIT:{record.getMessage()}"


class AuditFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage() != "rejected"


def _config(path):
    return LogConfig(
        log_levels=["INFO", "ERROR"],
        log_dir=str(path),
        log_file_formats={"INFO": "%(message)s", "ERROR": "%(message)s"},
        log_file_format_types={"INFO": "NORMAL", "ERROR": "NORMAL"},
        extra_log_files={"INFO": False, "ERROR": False},
        console_level="INFO",
        console_format="%(message)s",
        colorize_console=False,
        log_date_format="%Y-%m-%d",
        log_email_notifier_enable=False,
        log_email_notifier_log_levels=[],
        log_email_notifier_log_format=1,
    )


@pytest.fixture
def logger_state():
    root = logging.getLogger()
    package = logging.getLogger("django_logging")
    audit = logging.getLogger("component_test.audit")
    original = {
        l: (list(l.handlers), l.level, l.propagate) for l in (root, package, audit)
    }
    yield
    for owner, (handlers, level, propagate) in original.items():
        for h in list(owner.handlers):
            if h not in handlers:
                owner.removeHandler(h)
                h.close()
        for h in handlers:
            if h not in owner.handlers:
                owner.addHandler(h)
        owner.setLevel(level)
        owner.propagate = propagate


def test_dynamic_handler_formatter_filter_and_logger(tmp_path, logger_state):
    output = tmp_path / "audit.log"
    conf = _config(tmp_path)
    conf.components = {
        "formatters": {"audit_formatter": {"()": AuditFormatter}},
        "filters": {"audit_filter": {"()": AuditFilter}},
        "handlers": {
            "audit": {
                "class": "logging.FileHandler",
                "filename": str(output),
                "formatter": "audit_formatter",
                "filters": ["audit_filter"],
            }
        },
        "loggers": {
            "component_test.audit": {
                "handlers": ["audit"],
                "filters": ["audit_filter"],
                "level": "INFO",
                "propagate": False,
            }
        },
    }
    manager = LogManager(conf)
    manager.create_log_files()
    mapping = manager.build_logging_dict()
    assert "audit" in mapping["handlers"]
    manager.set_conf(mode="additive")
    logger = logging.getLogger("component_test.audit")
    logger.info("allowed")
    logger.info("rejected")
    assert output.read_text().splitlines() == ["AUDIT:allowed"]
    manager.set_conf(mode="additive")
    logger.info("only once")
    assert output.read_text().count("only once") == 1
    assert len([f for f in logger.filters if isinstance(f, AuditFilter)]) == 1


def test_explicit_builtin_replacement_and_disable(tmp_path, logger_state):
    conf = _config(tmp_path)
    conf.components = {
        "replace": {
            "handlers": {
                "info": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(tmp_path / "custom.log"),
                    "maxBytes": 1024,
                    "backupCount": 2,
                    "formatter": "info",
                    "level": "INFO",
                    "filters": ["info"],
                }
            }
        },
        "disable": {"handlers": ["error"]},
    }
    manager = LogManager(conf)
    manager.create_log_files()
    spec = manager.build_logging_dict()
    assert spec["handlers"]["info"]["class"] == "logging.handlers.RotatingFileHandler"
    assert "error" not in spec["handlers"]
    assert "error" not in spec["root"]["handlers"]
    manager.set_conf(mode="isolated")
    assert any(
        isinstance(h, logging.handlers.RotatingFileHandler)
        for h in logging.getLogger("django_logging").handlers
    )


def test_missing_and_collision_rejected_before_activation(tmp_path):
    mgr = LogManager(_config(tmp_path))
    spec = mgr.build_logging_dict()
    for components in (
        {"handlers": {"info": {"class": "logging.NullHandler"}}},
        {
            "handlers": {
                "custom": {"class": "logging.NullHandler", "formatter": "unknown"}
            }
        },
        {"root_handlers": ["missing"]},
        {"replace": {"handlers": {"unknown": {"class": "logging.NullHandler"}}}},
        {"disable": {"formatters": ["info"]}},
    ):
        with pytest.raises(ComponentConfigurationError):
            compile_components(spec, components)


@override_settings(DJANGO_LOGGING={"COMPONENTS": {"root_handlers": ["does_not_exist"]}})
def test_django_check_rejects_broken_component_reference():
    assert "django_logging.E046_COMPONENTS" in {
        e.id for e in check_logging_components(None)
    }


def test_django_check_rejects_invalid_structure():
    with override_settings(DJANGO_LOGGING={"COMPONENTS": {"handlers": ["wrong"]}}):
        assert check_logging_components(None)


def test_custom_root_route_preserves_host_handlers(tmp_path, logger_state):
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    host = logging.NullHandler()
    root.addHandler(host)
    dest = tmp_path / "custom.log"
    conf = _config(tmp_path)
    conf.components = {
        "handlers": {"custom": {"class": "logging.FileHandler", "filename": str(dest)}},
        "root_handlers": ["custom"],
    }
    m = LogManager(conf)
    m.create_log_files()
    m.set_conf("additive")
    logging.getLogger("component_test.other").info("hello from application")
    assert "hello from application" in dest.read_text()
    assert host in root.handlers


def test_invalid_factory_does_not_replace_previous_handlers(tmp_path, logger_state):
    base = LogManager(_config(tmp_path))
    base.create_log_files()
    base.set_conf("isolated")
    pkg = logging.getLogger("django_logging")
    before = list(pkg.handlers)

    broken = _config(tmp_path)
    broken.components = {
        "handlers": {"broken": {"class": "this.module.does.not.exist"}},
        "package_handlers": ["broken"],
    }
    mgr = LogManager(broken)
    with pytest.raises((ImportError, AttributeError, ValueError)):
        mgr.set_conf("isolated")
    assert list(pkg.handlers) == before


def test_compiled_config_is_not_mutated_and_legacy_route_is_present(tmp_path):
    mgr = LogManager(_config(tmp_path))
    mgr.create_log_files()
    preset = mgr.build_logging_dict()
    extension = {"root_handlers": ["console"]}
    first = compile_components(preset, extension)
    second = compile_components(preset, extension)
    assert first == second
    assert preset["root"]["handlers"].count("console") == 1
    assert first["root"]["handlers"].count("console") == 1


def test_factory_and_named_handler_dependency(tmp_path, logger_state):
    conf = _config(tmp_path)
    conf.components = {
        "handlers": {
            "buffered": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 10,
                "target": "sink",
            },
            "sink": {"()": logging.NullHandler},
        },
        "package_handlers": ["buffered"],
    }
    mgr = LogManager(conf)
    mgr.create_log_files()
    mgr.set_conf("isolated")
    buffered = next(
        h
        for h in logging.getLogger("django_logging").handlers
        if h.name == "dj_logging:buffered"
    )
    assert isinstance(buffered, logging.handlers.MemoryHandler)
    assert isinstance(buffered.target, logging.NullHandler)


def test_unattached_components_are_not_instantiated(tmp_path, logger_state):
    class UnusedHandler(logging.Handler):
        def __init__(self):
            raise AssertionError("unused handler was constructed")

        def emit(self, record):
            pass

    class UnusedFormatter(logging.Formatter):
        def __init__(self):
            raise AssertionError("unused formatter was constructed")

    conf = _config(tmp_path)
    conf.components = {
        "formatters": {"unused_format": {"()": UnusedFormatter}},
        "handlers": {
            "unused_handler": {"()": UnusedHandler, "formatter": "unused_format"},
            "active_buffer": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 4,
                "target": "active_sink",
            },
            "active_sink": {"class": "logging.NullHandler"},
        },
        "package_handlers": ["active_buffer"],
    }
    manager = LogManager(conf)
    manager.create_log_files()
    manager.set_conf("isolated")
    package = logging.getLogger("django_logging")
    buffer = next(h for h in package.handlers if h.name == "dj_logging:active_buffer")
    assert isinstance(buffer, logging.handlers.MemoryHandler)
    assert isinstance(buffer.target, logging.NullHandler)
    assert not any(h.name == "dj_logging:unused_handler" for h in package.handlers)


def test_explicit_console_root_attachment_is_honored(tmp_path, logger_state):
    root = logging.getLogger()
    manager = LogManager(_config(tmp_path))
    manager.log_config.components = {"root_handlers": ["console"]}
    manager.create_log_files()
    manager.set_conf("additive")
    assert len([h for h in root.handlers if h.name == "dj_logging:console"]) == 1
    manager.set_conf("additive")
    assert len([h for h in root.handlers if h.name == "dj_logging:console"]) == 1
    manager.log_config.components = {}
    manager.set_conf("isolated")
    assert not any(h.name == "dj_logging:console" for h in root.handlers)


def test_dependent_handler_closed_after_reinitialization(tmp_path, logger_state):
    conf = _config(tmp_path)
    conf.components = {
        "handlers": {
            "buffer": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 3,
                "target": "file_sink",
            },
            "file_sink": {
                "class": "logging.FileHandler",
                "filename": str(tmp_path / "dependent.log"),
            },
        },
        "package_handlers": ["buffer"],
    }
    manager = LogManager(conf)
    manager.create_log_files()
    manager.set_conf("isolated")
    buffer = next(
        h
        for h in logging.getLogger("django_logging").handlers
        if h.name == "dj_logging:buffer"
    )
    dependent = buffer.target
    assert isinstance(dependent, logging.FileHandler)
    assert dependent.stream is not None
    conf.components = {}
    manager.set_conf("isolated")
    assert dependent.stream is None
