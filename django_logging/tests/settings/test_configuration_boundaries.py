"""Configuration validation, pure compilation, and transactional activation."""

import logging
from copy import deepcopy
from unittest.mock import patch

import pytest
from django.test import override_settings

from django_logging.settings import activation
from django_logging.settings.checks import (
    check_logging_components,
    check_logging_settings,
    check_rotation_settings,
)
from django_logging.settings.components import (
    ComponentConfigurationError,
    compile_components,
    validate_components,
)
from django_logging.settings.conf import LogConfig, LogManager
from django_logging.settings.request_logging import request_logging_errors
from django_logging.tests.settings.test_logging_isolation import config_for
from django_logging.utils.context_manager import config_setup
from django_logging.utils.get_conf import is_log_sql_queries_enabled
from django_logging.validators.config_validators import validate_email_notifier


@pytest.mark.parametrize(
    "components",
    [
        [],
        {1: {}},
        {"unknown": {}},
        {"replace": {1: {}}},
        {"disable": {"unknown": []}},
        {"handlers": {"bad": []}},
        {"replace": {"handlers": []}},
        {"root_handlers": "console"},
        {"package_handlers": ["console", "console"]},
    ],
)
def test_invalid_extension_shapes_fail_before_importing_factories(components):
    with pytest.raises(ComponentConfigurationError):
        validate_components(components)


@pytest.mark.parametrize(
    "extension",
    [
        {"disable": {"handlers": ["missing"]}},
        {"handlers": {"bad": {}}},
        {
            "handlers": {
                "bad": {"class": "logging.NullHandler", "()": logging.NullHandler}
            }
        },
        {"handlers": {"bad": {"class": "logging.NullHandler", "filters": ["missing"]}}},
        {"loggers": {"app.boundary": {"unknown": True}}},
        {"loggers": {"app.boundary": {"handlers": ["missing"]}}},
        {"loggers": {"app.boundary": {"filters": ["missing"]}}},
        {"loggers": {"app.boundary": {"propagate": "yes"}}},
        {"loggers": {"django_logging": {}}},
    ],
)
def test_invalid_component_references_fail_without_activation(tmp_path, extension):
    manager = LogManager(LogConfig(**config_for(tmp_path)))
    with pytest.raises(ComponentConfigurationError):
        compile_components(manager.build_logging_dict(), extension)
    assert not list(tmp_path.iterdir())


def test_invalid_builtin_root_reference_is_rejected(tmp_path):
    config = LogManager(LogConfig(**config_for(tmp_path))).build_logging_dict()
    config["root"]["handlers"] = ["missing"]
    with pytest.raises(ComponentConfigurationError, match="Root refers"):
        compile_components(config, {})


@pytest.mark.parametrize(
    "value",
    [
        {"MAX_DIAGNOSTIC_DEPTH": 0},
        {"EXCLUDED_PATHS": "wrong"},
        {"EXCLUDED_FIELDS": [None]},
        {"EXCLUDED_PATH_PREFIXES": ["relative"]},
        {"EXCLUDED_FIELDS_BY_PATH": []},
    ],
)
def test_invalid_request_policies_are_reported(value):
    assert request_logging_errors(value)


@pytest.mark.parametrize(
    "value",
    [
        {"MAX_CONCURRENT": 0},
        {"SMTP_TIMEOUT": 121},
        {"SMTP_TIMEOUT": True},
        {"unknown": True},
    ],
)
def test_notifier_limits_and_unknown_settings_are_reported(value):
    assert validate_email_notifier(value)


def test_system_checks_accept_complete_planned_graph_and_reject_bad_audit(tmp_path):
    with override_settings(
        DJANGO_LOGGING={
            "LOG_DIR": str(tmp_path / "not-created"),
            "LOG_SIZE_AUDIT_IN_REQUEST": "yes",
        }
    ):
        assert check_logging_components(None) == []
        assert any(
            error.id == "django_logging.E044_LOG_SIZE_AUDIT"
            for error in check_logging_settings(None)
        )
    assert not (tmp_path / "not-created").exists()
    assert isinstance(is_log_sql_queries_enabled(), bool)


def test_inherited_compression_conflicts_with_external_rotation():
    with patch("django_logging.settings.checks.settings_manager") as current:
        current.log_rotation = {"TYPE": "size", "COMPRESS": True}
        current.log_rotation_overrides = {"INFO": {"TYPE": "external"}}
        assert any(
            error.id == "django_logging.E045_LOG_ROTATION_EFFECTIVE"
            for error in check_rotation_settings(None)
        )


def test_temporary_configuration_restores_named_routes_filters_and_dependencies(
    tmp_path,
):
    options = config_for(tmp_path)
    target = logging.getLogger("temporary.audit")
    before = list(target.handlers), list(target.filters), target.level, target.propagate
    options["components"] = {
        "filters": {"audit_filter": {"()": "logging.Filter"}},
        "handlers": {
            "buffer": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 10,
                "target": "sink",
            },
            "sink": {
                "class": "logging.FileHandler",
                "filename": str(tmp_path / "sink.log"),
            },
        },
        "loggers": {
            target.name: {
                "handlers": ["buffer"],
                "filters": ["audit_filter"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
    }
    with (
        patch(
            "django_logging.utils.context_manager.is_auto_initialization_enabled",
            return_value=False,
        ),
        patch("django_logging.utils.context_manager.get_config", return_value=options),
    ):
        with config_setup():
            buffer = target.handlers[-1]
            sink = buffer.target
            target.info("buffered audit")
            assert sink.stream is not None
            assert target.filters
        assert (
            list(target.handlers),
            list(target.filters),
            target.level,
            target.propagate,
        ) == before
        assert sink.stream is None
    assert "buffered audit" in (tmp_path / "sink.log").read_text()


def test_activation_rollback_restores_existing_handlers_filters_and_levels(tmp_path):
    options = config_for(tmp_path)
    options["components"] = {
        "filters": {"f": {"()": "logging.Filter"}},
        "loggers": {
            "rollback.audit": {"handlers": ["info"], "filters": ["f"], "level": "INFO"}
        },
    }
    manager = LogManager(LogConfig(**options))
    config = manager.build_logging_dict()
    logger = logging.getLogger("rollback.audit")
    with activation.temporary_activation(config, resolver=manager._resolve_class):
        before = (
            list(logger.handlers),
            list(logger.filters),
            logger.level,
            logger.propagate,
        )
        failed = deepcopy(config)
        failed["loggers"][logger.name]["level"] = "invalid level"
        with pytest.raises(ValueError):
            activation.activate(
                failed, mode="isolated", resolver=manager._resolve_class
            )
        assert (
            list(logger.handlers),
            list(logger.filters),
            logger.level,
            logger.propagate,
        ) == before
        logger.info("still usable")
    assert "still usable" in (tmp_path / "info.log").read_text()


def test_activation_rejects_cycles_invalid_modes_and_bad_factory_outputs(tmp_path):
    manager = LogManager(LogConfig(**config_for(tmp_path)))
    config = manager.build_logging_dict()
    with pytest.raises(ValueError, match="Unsupported"):
        activation.activate(config, mode="invalid", resolver=manager._resolve_class)
    config["handlers"].update(
        {
            "a": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 1,
                "target": "b",
            },
            "b": {
                "class": "logging.handlers.MemoryHandler",
                "capacity": 1,
                "target": "a",
            },
        }
    )
    config["_dj_package_handlers"] = ["a"]
    with pytest.raises(ValueError, match="cycle"):
        activation.activate(config, mode="isolated", resolver=manager._resolve_class)
    config["handlers"]["a"] = {"()": object}
    with pytest.raises(TypeError, match="did not produce"):
        activation.activate(config, mode="isolated", resolver=manager._resolve_class)


def test_handler_list_dependencies_are_constructed_before_parent(tmp_path):
    config = LogManager(LogConfig(**config_for(tmp_path))).build_logging_dict()
    constructed = []

    def sink():
        constructed.append("sink")
        return logging.NullHandler()

    def parent(handlers):
        assert handlers == ["sink"]
        assert constructed == ["sink"]
        constructed.append("parent")
        return logging.NullHandler()

    config["handlers"].update(
        {"parent": {"()": parent, "handlers": ["sink"]}, "sink": {"()": sink}}
    )
    config["_dj_package_handlers"] = ["parent"]
    with activation.temporary_activation(config, resolver=LogManager._resolve_class):
        assert constructed == ["sink", "parent"]


def test_legacy_isolated_helper_and_import_errors(tmp_path):
    config = LogManager(LogConfig(**config_for(tmp_path))).build_logging_dict()
    with patch.object(LogManager, "_set_owned_conf") as activate:
        LogManager._set_isolated_conf(config)
        activate.assert_called_once_with(config, mode="isolated")
    with pytest.raises(ValueError, match="Invalid import path"):
        LogManager._resolve_class("NotQualified")


def test_dotted_formatter_factory_is_resolved_and_used(tmp_path):
    config = LogManager(LogConfig(**config_for(tmp_path))).build_logging_dict()
    config["formatters"]["info"] = {"()": "logging.Formatter", "format": "%(message)s"}
    with activation.temporary_activation(config, resolver=LogManager._resolve_class):
        logging.getLogger("django_logging").info("custom formatter")
    assert "custom formatter" in (tmp_path / "info.log").read_text()
