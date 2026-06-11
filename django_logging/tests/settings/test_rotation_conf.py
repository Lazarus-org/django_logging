"""Tests for rotation-aware LogConfig and LogManager."""
import logging
import logging.handlers
import sys
from shutil import rmtree
from unittest import mock

import pytest

from django_logging.settings.conf import LogConfig, LogManager
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.settings,
    pytest.mark.settings_rotation_conf,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_log_config(**rotation_kwargs) -> LogConfig:
    """Return a minimal LogConfig, injecting rotation kwargs."""
    return LogConfig(
        log_levels=["INFO", "ERROR"],
        log_dir="/tmp/logs",
        log_file_formats={"INFO": 1, "ERROR": 1},
        log_file_format_types={"INFO": "NORMAL", "ERROR": "NORMAL"},
        extra_log_files={"INFO": False, "ERROR": False},
        console_level="INFO",
        console_format=1,
        colorize_console=False,
        log_date_format="%Y-%m-%d %H:%M:%S",
        log_email_notifier_enable=False,
        log_email_notifier_log_levels=[None, None],
        log_email_notifier_log_format=1,
        **rotation_kwargs,
    )


# ---------------------------------------------------------------------------
# LogConfig — rotation config merging
# ---------------------------------------------------------------------------

class TestLogConfigRotation:

    def test_default_rotation_type_is_none(self):
        """When no rotation is given the default TYPE is 'none'."""
        config = make_log_config()
        assert config.log_rotation["TYPE"] == "none"

    def test_custom_global_rotation_is_stored(self):
        """Global rotation config is stored and accessible."""
        rotation = {"TYPE": "size", "MAX_BYTES": 5_000_000, "BACKUP_COUNT": 10}
        config = make_log_config(log_rotation=rotation)
        assert config.log_rotation["TYPE"] == "size"
        assert config.log_rotation["MAX_BYTES"] == 5_000_000

    def test_per_level_override_merges_over_global(self):
        """Per-level override merges its keys on top of the global config."""
        global_rotation = {"TYPE": "size", "MAX_BYTES": 1_000_000, "BACKUP_COUNT": 5}
        overrides = {
            "ERROR": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 30},
        }
        config = make_log_config(
            log_rotation=global_rotation,
            log_rotation_overrides=overrides,
        )

        # ERROR should use time-based rotation
        error_cfg = config.get_rotation_config_for_level("ERROR")
        assert error_cfg["TYPE"] == "time"
        assert error_cfg["WHEN"] == "midnight"
        assert error_cfg["BACKUP_COUNT"] == 30

        # INFO should still use the global size-based rotation
        info_cfg = config.get_rotation_config_for_level("INFO")
        assert info_cfg["TYPE"] == "size"
        assert info_cfg["BACKUP_COUNT"] == 5

    def test_override_partial_keys_inherits_rest_from_global(self):
        """A partial override only changes the specified keys."""
        global_rotation = {
            "TYPE": "size",
            "MAX_BYTES": 2_000_000,
            "BACKUP_COUNT": 7,
            "COMPRESS": True,
        }
        # Override only BACKUP_COUNT for ERROR
        overrides = {"ERROR": {"BACKUP_COUNT": 90}}
        config = make_log_config(
            log_rotation=global_rotation,
            log_rotation_overrides=overrides,
        )

        error_cfg = config.get_rotation_config_for_level("ERROR")
        assert error_cfg["TYPE"] == "size"          # inherited
        assert error_cfg["MAX_BYTES"] == 2_000_000  # inherited
        assert error_cfg["BACKUP_COUNT"] == 90      # overridden
        assert error_cfg["COMPRESS"] is True        # inherited

    def test_level_with_no_override_returns_global(self):
        """Levels without an override entry return the unmodified global config."""
        config = make_log_config(
            log_rotation={"TYPE": "time", "WHEN": "h", "BACKUP_COUNT": 24},
        )
        info_cfg = config.get_rotation_config_for_level("INFO")
        assert info_cfg["TYPE"] == "time"
        assert info_cfg["WHEN"] == "h"


# ---------------------------------------------------------------------------
# LogManager — _build_file_handler_config
# ---------------------------------------------------------------------------

class TestLogManagerHandlerFactory:

    def _make_manager(self, **rotation_kwargs) -> LogManager:
        return LogManager(make_log_config(**rotation_kwargs))

    def test_no_rotation_yields_plain_file_handler(self):
        """TYPE='none' → plain logging.FileHandler."""
        manager = self._make_manager()
        cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        assert cfg["class"] == "logging.FileHandler"
        assert "maxBytes" not in cfg
        assert "when" not in cfg

    def test_size_rotation_yields_rotating_handler(self):
        """TYPE='size' → RotatingFileHandler."""
        manager = self._make_manager(
            log_rotation={"TYPE": "size", "MAX_BYTES": 5_000_000, "BACKUP_COUNT": 3}
        )
        cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        assert "RotatingFileHandler" in cfg["class"]
        assert cfg["maxBytes"] == 5_000_000
        assert cfg["backupCount"] == 3

    def test_size_rotation_compress_yields_compressed_handler(self):
        """TYPE='size' + COMPRESS=True → CompressedRotatingFileHandler."""
        manager = self._make_manager(
            log_rotation={"TYPE": "size", "MAX_BYTES": 1_000_000, "BACKUP_COUNT": 5, "COMPRESS": True}
        )
        cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        assert "CompressedRotatingFileHandler" in cfg["class"]

    def test_time_rotation_yields_timed_handler(self):
        """TYPE='time' → TimedRotatingFileHandler."""
        manager = self._make_manager(
            log_rotation={"TYPE": "time", "WHEN": "midnight", "INTERVAL": 1, "BACKUP_COUNT": 7}
        )
        cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        assert "TimedRotatingFileHandler" in cfg["class"]
        assert cfg["when"] == "midnight"
        assert cfg["interval"] == 1
        assert cfg["backupCount"] == 7

    def test_time_rotation_compress_yields_compressed_handler(self):
        """TYPE='time' + COMPRESS=True → CompressedTimedRotatingFileHandler."""
        manager = self._make_manager(
            log_rotation={"TYPE": "time", "WHEN": "midnight", "COMPRESS": True, "BACKUP_COUNT": 5}
        )
        cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        assert "CompressedTimedRotatingFileHandler" in cfg["class"]

    def test_per_level_override_used_in_handler_config(self):
        """Per-level override is respected by the handler factory."""
        overrides = {"ERROR": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 30}}
        manager = self._make_manager(
            log_rotation={"TYPE": "size", "MAX_BYTES": 1_000_000, "BACKUP_COUNT": 5},
            log_rotation_overrides=overrides,
        )

        info_cfg = manager._build_file_handler_config("/tmp/logs/info.log", "INFO")
        error_cfg = manager._build_file_handler_config("/tmp/logs/error.log", "ERROR")

        assert "RotatingFileHandler" in info_cfg["class"]
        assert "TimedRotatingFileHandler" in error_cfg["class"]
        assert error_cfg["when"] == "midnight"

    # ------------------------------------------------------------------
    # set_conf integration
    # ------------------------------------------------------------------

    def test_set_conf_uses_rotating_handler_class_in_config(self):
        """set_conf passes the correct rotating handler class to dictConfig."""
        manager = self._make_manager(
            log_rotation={"TYPE": "size", "MAX_BYTES": 5_000_000, "BACKUP_COUNT": 3}
        )
        with mock.patch("os.makedirs"), mock.patch("builtins.open", mock.mock_open()), \
             mock.patch("os.path.exists", return_value=False):
            manager.create_log_files()

        with mock.patch("logging.config.dictConfig") as dict_config_mock:
            manager.set_conf()

        config = dict_config_mock.call_args[0][0]
        for level in ("info", "error"):
            handler = config["handlers"][level]
            assert "RotatingFileHandler" in handler["class"], (
                f"Expected RotatingFileHandler for {level}, got {handler['class']}"
            )
            assert "maxBytes" in handler
            assert "backupCount" in handler

    def test_set_conf_uses_timed_handler_class_in_config(self):
        """set_conf uses TimedRotatingFileHandler when TYPE='time'."""
        manager = self._make_manager(
            log_rotation={"TYPE": "time", "WHEN": "midnight", "INTERVAL": 1, "BACKUP_COUNT": 5}
        )
        with mock.patch("os.makedirs"), mock.patch("builtins.open", mock.mock_open()), \
             mock.patch("os.path.exists", return_value=False):
            manager.create_log_files()

        with mock.patch("logging.config.dictConfig") as dict_config_mock:
            manager.set_conf()

        config = dict_config_mock.call_args[0][0]
        for level in ("info", "error"):
            handler = config["handlers"][level]
            assert "TimedRotatingFileHandler" in handler["class"]
            assert handler["when"] == "midnight"

        rmtree("/tmp", ignore_errors=True)
