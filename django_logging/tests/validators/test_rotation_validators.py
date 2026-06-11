"""Tests for rotation config validators."""
import sys
from typing import List

import pytest
from django.core.checks import Error

from django_logging.validators.config_validators import (
    validate_rotation_config,
    validate_rotation_overrides,
)
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.validators,
    pytest.mark.validators_rotation,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]

VALID_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class TestValidateRotationConfig:

    # ------------------------------------------------------------------
    # Valid configs
    # ------------------------------------------------------------------

    def test_empty_dict_is_valid(self):
        """An empty dict (all defaults) must not produce errors."""
        errors = validate_rotation_config({}, "LOG_ROTATION", VALID_LEVELS)
        assert not errors

    def test_type_none_is_valid(self):
        errors = validate_rotation_config({"TYPE": "none"}, "LOG_ROTATION", VALID_LEVELS)
        assert not errors

    def test_type_size_full_config_is_valid(self):
        errors = validate_rotation_config(
            {"TYPE": "size", "MAX_BYTES": 10_485_760, "BACKUP_COUNT": 5, "COMPRESS": False},
            "LOG_ROTATION",
            VALID_LEVELS,
        )
        assert not errors

    def test_type_time_full_config_is_valid(self):
        errors = validate_rotation_config(
            {"TYPE": "time", "WHEN": "midnight", "INTERVAL": 1, "BACKUP_COUNT": 7, "COMPRESS": True},
            "LOG_ROTATION",
            VALID_LEVELS,
        )
        assert not errors

    def test_all_valid_when_values(self):
        valid_whens = ["s", "m", "h", "d", "midnight", "w0", "w1", "w2", "w3", "w4", "w5", "w6"]
        for when in valid_whens:
            errors = validate_rotation_config(
                {"TYPE": "time", "WHEN": when}, "LOG_ROTATION", VALID_LEVELS
            )
            assert not any("E034" in e.id for e in errors), f"WHEN={when!r} should be valid"

    # ------------------------------------------------------------------
    # Not a dict
    # ------------------------------------------------------------------

    def test_non_dict_raises_e030(self):
        errors = validate_rotation_config("size", "LOG_ROTATION", VALID_LEVELS)  # type: ignore
        assert any("E030" in e.id for e in errors)

    # ------------------------------------------------------------------
    # TYPE errors
    # ------------------------------------------------------------------

    def test_invalid_type_raises_e031(self):
        errors = validate_rotation_config({"TYPE": "weekly"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E031" in e.id for e in errors)

    def test_case_insensitive_type(self):
        """TYPE comparison is case-insensitive."""
        errors = validate_rotation_config({"TYPE": "SIZE"}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E031" in e.id for e in errors)

    # ------------------------------------------------------------------
    # MAX_BYTES errors
    # ------------------------------------------------------------------

    def test_max_bytes_zero_raises_e032(self):
        errors = validate_rotation_config({"MAX_BYTES": 0}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E032" in e.id for e in errors)

    def test_max_bytes_negative_raises_e032(self):
        errors = validate_rotation_config({"MAX_BYTES": -1}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E032" in e.id for e in errors)

    def test_max_bytes_string_raises_e032(self):
        errors = validate_rotation_config({"MAX_BYTES": "10mb"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E032" in e.id for e in errors)

    def test_max_bytes_valid(self):
        errors = validate_rotation_config({"MAX_BYTES": 1}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E032" in e.id for e in errors)

    # ------------------------------------------------------------------
    # BACKUP_COUNT errors
    # ------------------------------------------------------------------

    def test_backup_count_negative_raises_e033(self):
        errors = validate_rotation_config({"BACKUP_COUNT": -1}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E033" in e.id for e in errors)

    def test_backup_count_zero_is_valid(self):
        errors = validate_rotation_config({"BACKUP_COUNT": 0}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E033" in e.id for e in errors)

    def test_backup_count_string_raises_e033(self):
        errors = validate_rotation_config({"BACKUP_COUNT": "five"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E033" in e.id for e in errors)

    # ------------------------------------------------------------------
    # WHEN errors
    # ------------------------------------------------------------------

    def test_invalid_when_raises_e034(self):
        errors = validate_rotation_config({"WHEN": "monthly"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E034" in e.id for e in errors)

    def test_when_case_insensitive(self):
        """WHEN comparison is case-insensitive."""
        errors = validate_rotation_config({"WHEN": "MIDNIGHT"}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E034" in e.id for e in errors)

    # ------------------------------------------------------------------
    # INTERVAL errors
    # ------------------------------------------------------------------

    def test_interval_zero_raises_e035(self):
        errors = validate_rotation_config({"INTERVAL": 0}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E035" in e.id for e in errors)

    def test_interval_negative_raises_e035(self):
        errors = validate_rotation_config({"INTERVAL": -2}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E035" in e.id for e in errors)

    def test_interval_string_raises_e035(self):
        errors = validate_rotation_config({"INTERVAL": "daily"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E035" in e.id for e in errors)

    def test_interval_positive_is_valid(self):
        errors = validate_rotation_config({"INTERVAL": 1}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E035" in e.id for e in errors)

    # ------------------------------------------------------------------
    # COMPRESS errors
    # ------------------------------------------------------------------

    def test_compress_string_raises_e036(self):
        errors = validate_rotation_config({"COMPRESS": "yes"}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E036" in e.id for e in errors)

    def test_compress_int_raises_e036(self):
        errors = validate_rotation_config({"COMPRESS": 1}, "LOG_ROTATION", VALID_LEVELS)
        assert any("E036" in e.id for e in errors)

    def test_compress_true_is_valid(self):
        errors = validate_rotation_config({"COMPRESS": True}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E036" in e.id for e in errors)

    def test_compress_false_is_valid(self):
        errors = validate_rotation_config({"COMPRESS": False}, "LOG_ROTATION", VALID_LEVELS)
        assert not any("E036" in e.id for e in errors)

    # ------------------------------------------------------------------
    # Multiple errors at once
    # ------------------------------------------------------------------

    def test_multiple_invalid_fields_all_reported(self):
        """All validation errors for a single config dict are collected."""
        errors = validate_rotation_config(
            {"TYPE": "bad", "MAX_BYTES": -1, "BACKUP_COUNT": -5, "COMPRESS": "nope"},
            "LOG_ROTATION",
            VALID_LEVELS,
        )
        ids = [e.id for e in errors]
        assert any("E031" in i for i in ids)
        assert any("E032" in i for i in ids)
        assert any("E033" in i for i in ids)
        assert any("E036" in i for i in ids)


class TestValidateRotationOverrides:

    def test_empty_overrides_is_valid(self):
        errors = validate_rotation_overrides({}, "LOG_ROTATION_OVERRIDES", VALID_LEVELS)
        assert not errors

    def test_valid_override_per_level(self):
        overrides = {
            "ERROR": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 30},
            "CRITICAL": {"TYPE": "size", "MAX_BYTES": 5_000_000},
        }
        errors = validate_rotation_overrides(overrides, "LOG_ROTATION_OVERRIDES", VALID_LEVELS)
        assert not errors

    def test_non_dict_raises_e037(self):
        errors = validate_rotation_overrides(
            "not a dict", "LOG_ROTATION_OVERRIDES", VALID_LEVELS  # type: ignore
        )
        assert any("E037" in e.id for e in errors)

    def test_invalid_level_key_raises_e038(self):
        errors = validate_rotation_overrides(
            {"TRACE": {"TYPE": "size"}}, "LOG_ROTATION_OVERRIDES", VALID_LEVELS
        )
        assert any("E038" in e.id for e in errors)

    def test_invalid_sub_config_propagates_inner_error(self):
        """Errors inside a per-level sub-config are surfaced with the level in the name."""
        overrides = {"ERROR": {"TYPE": "time", "WHEN": "quarterly"}}
        errors = validate_rotation_overrides(overrides, "LOG_ROTATION_OVERRIDES", VALID_LEVELS)
        assert any("E034" in e.id for e in errors)
        # The config_name in the error id should reference the level
        assert any("ERROR" in e.id for e in errors)

    def test_multiple_invalid_levels_all_reported(self):
        overrides = {
            "INFO": {"WHEN": "monthly"},      # bad WHEN
            "DEBUG": {"MAX_BYTES": -100},     # bad MAX_BYTES
            "NOTREAL": {"TYPE": "size"},      # bad level key
        }
        errors = validate_rotation_overrides(overrides, "LOG_ROTATION_OVERRIDES", VALID_LEVELS)
        ids = [e.id for e in errors]
        assert any("E034" in i for i in ids)   # bad WHEN
        assert any("E032" in i for i in ids)   # bad MAX_BYTES
        assert any("E038" in i for i in ids)   # bad level key
