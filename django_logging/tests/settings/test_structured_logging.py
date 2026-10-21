"""Django integration for structured formatter configuration."""

import logging

import pytest
from django.test import override_settings

from django_logging.settings.checks import check_structured_logging_settings
from django_logging.settings.conf import LogManager
from django_logging.settings.manager import SettingsManager


def test_log_manager_passes_structured_options(log_config):
    log_config.log_file_format_types["INFO"] = "JSON"
    log_config.structured_logging["EXCEPTION_MODE"] = "type"
    log_manager = LogManager(log_config)
    log_manager.log_files = {"INFO": "/tmp/info.log"}
    config = log_manager.build_logging_dict()
    args = config["formatters"]["info"]
    assert args["()"] == "django_logging.formatters.JSONFormatter"
    assert args["structured_logging"]["EXCEPTION_MODE"] == "type"
    formatter = __import__(
        "django_logging.formatters", fromlist=["JSONFormatter"]
    ).JSONFormatter(
        fmt=args["format"],
        datefmt=args["datefmt"],
        structured_logging=args["structured_logging"],
    )
    item = logging.LogRecord("app", logging.INFO, __file__, 1, "hi", (), None)
    assert '"message":"hi"' in formatter.format(item)


@override_settings(
    DJANGO_LOGGING={
        "AUTO_INITIALIZATION_ENABLE": False,
        "STRUCTURED_LOGGING": {"MAX_DEPTH": 0},
    }
)
def test_invalid_settings_report_system_check_error():
    errors = check_structured_logging_settings(None)
    assert any(e.id == "django_logging.E042_STRUCTURED_LOGGING" for e in errors)


@override_settings(
    DJANGO_LOGGING={
        "AUTO_INITIALIZATION_ENABLE": False,
        "STRUCTURED_LOGGING": {"REDACT_FIELDS": ["employee_id"]},
    }
)
def test_settings_manager_exposes_existing_namespace():
    assert SettingsManager().structured_logging["REDACT_FIELDS"] == ["employee_id"]
