"""Tests for the rotation-related system checks."""
import sys
from typing import List
from unittest.mock import patch

import pytest
from django.core.checks import Error

from django_logging.settings import settings_manager
from django_logging.settings.checks import check_rotation_settings
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.settings,
    pytest.mark.settings_rotation_checks,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestRotationChecks:

    # ------------------------------------------------------------------
    # Valid configs — expect zero errors
    # ------------------------------------------------------------------

    def test_valid_rotation_none(self, reset_settings):
        """TYPE='none' (default) produces no errors."""
        settings_manager.log_rotation = {"TYPE": "none"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not errors

    def test_valid_rotation_size(self, reset_settings):
        """A complete TYPE='size' config produces no errors."""
        settings_manager.log_rotation = {
            "TYPE": "size",
            "MAX_BYTES": 10_485_760,
            "BACKUP_COUNT": 5,
            "COMPRESS": False,
        }
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not errors

    def test_valid_rotation_time(self, reset_settings):
        """A complete TYPE='time' config produces no errors."""
        settings_manager.log_rotation = {
            "TYPE": "time",
            "WHEN": "midnight",
            "INTERVAL": 1,
            "BACKUP_COUNT": 7,
            "COMPRESS": True,
        }
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not errors

    def test_valid_overrides(self, reset_settings):
        """Per-level overrides with valid configs produce no errors."""
        settings_manager.log_rotation = {"TYPE": "size", "MAX_BYTES": 5_000_000, "BACKUP_COUNT": 5}
        settings_manager.log_rotation_overrides = {
            "ERROR": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 30},
            "CRITICAL": {"TYPE": "time", "WHEN": "W0", "BACKUP_COUNT": 90},
        }
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not errors

    # ------------------------------------------------------------------
    # Invalid TYPE
    # ------------------------------------------------------------------

    def test_invalid_rotation_type(self, reset_settings):
        """An unknown TYPE value raises E031."""
        settings_manager.log_rotation = {"TYPE": "hourly"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E031" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Invalid MAX_BYTES
    # ------------------------------------------------------------------

    def test_invalid_max_bytes_zero(self, reset_settings):
        """MAX_BYTES=0 is not valid — raises E032."""
        settings_manager.log_rotation = {"TYPE": "size", "MAX_BYTES": 0}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E032" in e.id for e in errors)

    def test_invalid_max_bytes_negative(self, reset_settings):
        """Negative MAX_BYTES raises E032."""
        settings_manager.log_rotation = {"TYPE": "size", "MAX_BYTES": -1024}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E032" in e.id for e in errors)

    def test_invalid_max_bytes_string(self, reset_settings):
        """A non-integer MAX_BYTES raises E032."""
        settings_manager.log_rotation = {"TYPE": "size", "MAX_BYTES": "10mb"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E032" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Invalid BACKUP_COUNT
    # ------------------------------------------------------------------

    def test_invalid_backup_count_negative(self, reset_settings):
        """Negative BACKUP_COUNT raises E033."""
        settings_manager.log_rotation = {"TYPE": "size", "BACKUP_COUNT": -1}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E033" in e.id for e in errors)

    def test_backup_count_zero_is_valid(self, reset_settings):
        """BACKUP_COUNT=0 means keep all rotated files and is allowed."""
        settings_manager.log_rotation = {"TYPE": "size", "BACKUP_COUNT": 0}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not any("E033" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Invalid WHEN
    # ------------------------------------------------------------------

    def test_invalid_when_value(self, reset_settings):
        """An unsupported WHEN value raises E034."""
        settings_manager.log_rotation = {"TYPE": "time", "WHEN": "monthly"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E034" in e.id for e in errors)

    def test_valid_when_weekday(self, reset_settings):
        """WHEN='W3' (Wednesday) is valid."""
        settings_manager.log_rotation = {"TYPE": "time", "WHEN": "W3"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert not any("E034" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Invalid INTERVAL
    # ------------------------------------------------------------------

    def test_invalid_interval_zero(self, reset_settings):
        """INTERVAL=0 is not a positive integer — raises E035."""
        settings_manager.log_rotation = {"TYPE": "time", "INTERVAL": 0}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E035" in e.id for e in errors)

    def test_invalid_interval_negative(self, reset_settings):
        """Negative INTERVAL raises E035."""
        settings_manager.log_rotation = {"TYPE": "time", "INTERVAL": -3}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E035" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Invalid COMPRESS
    # ------------------------------------------------------------------

    def test_invalid_compress_string(self, reset_settings):
        """COMPRESS='yes' (non-boolean) raises E036."""
        settings_manager.log_rotation = {"TYPE": "size", "COMPRESS": "yes"}
        settings_manager.log_rotation_overrides = {}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E036" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Overrides validation
    # ------------------------------------------------------------------

    def test_invalid_level_in_overrides(self, reset_settings):
        """An unknown log level key in LOG_ROTATION_OVERRIDES raises E038."""
        settings_manager.log_rotation = {"TYPE": "none"}
        settings_manager.log_rotation_overrides = {"VERBOSE": {"TYPE": "size"}}
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E038" in e.id for e in errors)

    def test_invalid_config_in_override_level(self, reset_settings):
        """Invalid sub-config inside an override raises the appropriate error."""
        settings_manager.log_rotation = {"TYPE": "none"}
        settings_manager.log_rotation_overrides = {
            "ERROR": {"TYPE": "time", "WHEN": "invalid_when"}
        }
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E034" in e.id for e in errors)

    def test_overrides_not_a_dict_raises_e037(self, reset_settings):
        """Non-dict LOG_ROTATION_OVERRIDES raises E037."""
        settings_manager.log_rotation = {"TYPE": "none"}
        settings_manager.log_rotation_overrides = ["ERROR", "CRITICAL"]  # type: ignore
        errors: List[Error] = check_rotation_settings(None)  # type: ignore
        assert any("E037" in e.id for e in errors)
