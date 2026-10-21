"""Configuration isolation and explicit legacy compatibility tests."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import override_settings

from django_logging.constants import DefaultLoggingSettings
from django_logging.settings.checks import check_logging_settings
from django_logging.settings.conf import LogConfig, LogManager
from django_logging.settings.manager import SettingsManager
from django_logging.utils.set_conf import set_config


def config_for(log_dir: Path):
    return {
        "log_levels": ["INFO", "ERROR"],
        "log_dir": str(log_dir),
        "log_file_formats": {"INFO": "%(message)s", "ERROR": "%(message)s"},
        "log_file_format_types": {"INFO": "NORMAL", "ERROR": "NORMAL"},
        "extra_log_files": {"INFO": False, "ERROR": False},
        "console_level": "INFO",
        "console_format": "%(message)s",
        "colorize_console": False,
        "log_date_format": "%Y-%m-%d %H:%M:%S",
        "log_email_notifier_enable": False,
        "log_email_notifier_log_levels": [],
        "log_email_notifier_log_format": 1,
    }


@pytest.fixture
def preserve_loggers():
    root = logging.getLogger()
    pkg = logging.getLogger("django_logging")
    external = logging.getLogger("myapp.service")
    saved = [
        (logger, list(logger.handlers), logger.level, logger.propagate)
        for logger in [root, pkg, external]
    ]
    # The repository's test Django setup may already initialize logging.
    # Detach without closing those handles so they can be restored afterward.
    for handler in list(pkg.handlers):
        if getattr(handler, "_dj_logging_owned", False):
            pkg.removeHandler(handler)
    yield root, pkg, external
    for logger, original, level, propagate in saved:
        for handler in list(logger.handlers):
            if handler not in original:
                logger.removeHandler(handler)
                handler.close()
        for handler in original:
            if handler not in logger.handlers:
                logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = propagate


def test_default_automatically_initializes_additively():
    assert DefaultLoggingSettings().auto_initialization_enable is True
    assert DefaultLoggingSettings().logging_setup_mode == "additive"
    with override_settings(DJANGO_LOGGING={}):
        fresh = SettingsManager()
        assert fresh.auto_initialization_enabled is True
        assert fresh.logging_setup_mode == "additive"


def test_isolated_installs_no_root_or_external_changes(tmp_path, preserve_loggers):
    root, pkg, external = preserve_loggers
    sentinel = logging.NullHandler()
    root.addHandler(sentinel)
    external_sentinel = logging.NullHandler()
    external.addHandler(external_sentinel)
    external.setLevel(logging.ERROR)
    before = list(root.handlers), root.level, list(external.handlers), external.level
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    with patch(
        "logging.config.dictConfig", side_effect=AssertionError("dictConfig used")
    ):
        m.set_conf(mode="isolated")
        assert (
            list(root.handlers),
            root.level,
            list(external.handlers),
            external.level,
        ) == before
        assert pkg.propagate is False
        assert pkg.level == logging.DEBUG
        assert any(getattr(h, "_dj_logging_owned", False) for h in pkg.handlers)
        assert all(
            h not in root.handlers
            for h in pkg.handlers
            if getattr(h, "_dj_logging_owned", False)
        )
        logging.getLogger("django_logging.tests.example").info("test line")
        assert "test line" in (tmp_path / "info.log").read_text()


def test_isolated_repeated_setup_does_not_accumulate_handlers(
    tmp_path, preserve_loggers
):
    _, pkg, _ = preserve_loggers
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    m.set_conf(mode="isolated")
    old = [h for h in pkg.handlers if getattr(h, "_dj_logging_owned", False)]
    m.set_conf(mode="isolated")
    new = [h for h in pkg.handlers if getattr(h, "_dj_logging_owned", False)]
    assert len(old) == len(new) == 3
    assert not any(h in new for h in old)
    assert all(h.stream is None for h in old if isinstance(h, logging.FileHandler))


def test_failed_handler_setup_leaves_existing_handlers_untouched(
    tmp_path, preserve_loggers
):
    root, pkg, _ = preserve_loggers
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    m.set_conf(mode="isolated")
    before = list(pkg.handlers)
    root_before = list(root.handlers)
    with patch.object(
        LogManager, "_resolve_class", side_effect=ImportError("invalid handler")
    ):
        with pytest.raises(ImportError, match="invalid handler"):
            m.set_conf(mode="isolated")
    assert list(pkg.handlers) == before
    assert list(root.handlers) == root_before


def test_build_config_is_pure(tmp_path, preserve_loggers):
    root, package, external = preserve_loggers
    before = (
        list(root.handlers),
        root.level,
        list(package.handlers),
        package.level,
        list(external.handlers),
        external.level,
    )
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    mapping = m.build_logging_dict()
    assert mapping["version"] == 1
    assert (
        list(root.handlers),
        root.level,
        list(package.handlers),
        package.level,
        list(external.handlers),
        external.level,
    ) == before


def test_explicit_legacy_root_mode(tmp_path):
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    with patch("logging.config.dictConfig") as configure:
        m.set_conf(mode="replace_root")
    spec = configure.call_args.args[0]
    assert spec["root"]["level"] == "DEBUG"
    assert "console" in spec["root"]["handlers"]


def test_invalid_mode_is_rejected_without_mutation(tmp_path, preserve_loggers):
    root, pkg, _ = preserve_loggers
    m = LogManager(LogConfig(**config_for(tmp_path)))
    original = list(root.handlers), list(pkg.handlers)
    with pytest.raises(ValueError, match="mode"):
        m.set_conf(mode="clobber")
    assert (list(root.handlers), list(pkg.handlers)) == original


@override_settings(DJANGO_LOGGING={"LOGGING_SETUP_MODE": "invalid"})
def test_check_rejects_invalid_mode():
    errors = check_logging_settings(None)
    assert "django_logging.E041_LOGGING_SETUP_MODE" in {e.id for e in errors}


def test_set_config_rejects_bad_mode_before_creating_files(tmp_path):
    from django.core.exceptions import ImproperlyConfigured

    kwargs = config_for(tmp_path)
    with (
        patch(
            "django_logging.utils.set_conf.is_auto_initialization_enabled",
            return_value=True,
        ),
        patch(
            "django_logging.utils.set_conf.get_logging_setup_mode",
            return_value="not-a-mode",
        ),
        patch("django_logging.utils.set_conf.LogManager") as manager,
    ):
        with pytest.raises(ImproperlyConfigured, match="LOGGING_SETUP_MODE"):
            set_config(**kwargs)
        manager.assert_not_called()


def test_set_config_rejects_nonboolean_activation(tmp_path):
    from django.core.exceptions import ImproperlyConfigured

    kwargs = config_for(tmp_path)
    with (
        patch(
            "django_logging.utils.set_conf.is_auto_initialization_enabled",
            return_value="False",
        ),
        patch("django_logging.utils.set_conf.LogManager") as manager,
    ):
        with pytest.raises(ImproperlyConfigured, match="AUTO_INITIALIZATION_ENABLE"):
            set_config(**kwargs)
        manager.assert_not_called()


def test_additive_keeps_host_handlers_and_captures_app_logs(tmp_path, preserve_loggers):
    root, pkg, external = preserve_loggers
    sentinel = logging.NullHandler()
    root.addHandler(sentinel)
    root.setLevel(logging.INFO)
    external_sentinel = logging.NullHandler()
    external.addHandler(external_sentinel)
    external.setLevel(logging.INFO)
    external.propagate = True
    before = (root.level, list(root.handlers), external.level, list(external.handlers))
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    with patch(
        "logging.config.dictConfig", side_effect=AssertionError("dictConfig used")
    ):
        m.set_conf(mode="additive")
    assert root.level == before[0] and root.handlers[: len(before[1])] == before[1]
    assert external.level == before[2] and external.handlers == before[3]
    assert all(
        h.name != "dj_logging:console"
        for h in root.handlers
        if getattr(h, "_dj_logging_owned", False)
    )
    logging.getLogger("myapp.service").info("application event")
    logging.getLogger("django_logging.middleware.test").info("package event")
    logs = (tmp_path / "info.log").read_text()
    assert logs.count("application event") == 1
    assert logs.count("package event") == 1


def test_additive_reinitialization_and_switch_to_isolated(tmp_path, preserve_loggers):
    root, pkg, _ = preserve_loggers
    sentinel = logging.NullHandler()
    root.addHandler(sentinel)
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    m.set_conf(mode="additive")
    old = {h for h in root.handlers if getattr(h, "_dj_logging_owned", False)}
    assert len(old) == 2
    m.set_conf(mode="additive")
    latest = {h for h in root.handlers if getattr(h, "_dj_logging_owned", False)}
    assert len(latest) == 2 and not old & latest
    assert all(h.stream is None for h in old if isinstance(h, logging.FileHandler))
    m.set_conf(mode="isolated")
    assert not any(getattr(h, "_dj_logging_owned", False) for h in root.handlers)
    assert sentinel in root.handlers
    assert any(getattr(h, "_dj_logging_owned", False) for h in pkg.handlers)


def test_failed_additive_setup_preserves_existing_logging(tmp_path, preserve_loggers):
    root, pkg, _ = preserve_loggers
    m = LogManager(LogConfig(**config_for(tmp_path)))
    m.create_log_files()
    m.set_conf(mode="additive")
    before = (list(root.handlers), list(pkg.handlers), root.level)
    with patch.object(
        LogManager, "_resolve_class", side_effect=ImportError("broken formatter")
    ):
        with pytest.raises(ImportError, match="broken formatter"):
            m.set_conf(mode="additive")
    assert (list(root.handlers), list(pkg.handlers), root.level) == before


def test_auto_initialization_can_be_disabled():
    with override_settings(DJANGO_LOGGING={"AUTO_INITIALIZATION_ENABLE": False}):
        assert SettingsManager().auto_initialization_enabled is False
