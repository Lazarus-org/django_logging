"""Tests for the compressed rotating file handlers."""
import gzip
import logging
import logging.handlers
import os
import sys

import pytest

from django_logging.handlers.rotating_file_handler import (
    CompressedRotatingFileHandler,
    CompressedTimedRotatingFileHandler,
)
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.handlers,
    pytest.mark.handlers_rotating,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestCompressedRotatingFileHandler:

    def test_rollover_produces_gz_file(self, tmp_path):
        """After rollover, the rotated file has a .gz extension."""
        log_file = str(tmp_path / "app.log")
        handler = CompressedRotatingFileHandler(log_file, maxBytes=10, backupCount=3)
        handler.setLevel(logging.DEBUG)

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="hello world trigger rotation", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.doRollover()
        handler.close()

        rotated_files = [f for f in os.listdir(tmp_path) if f != "app.log"]
        assert any(f.endswith(".gz") for f in rotated_files), (
            f"Expected a .gz file in {list(os.listdir(tmp_path))}"
        )

    def test_rotated_gz_file_is_valid_gzip(self, tmp_path):
        """The .gz file produced on rollover is a valid gzip archive."""
        log_file = str(tmp_path / "app.log")
        handler = CompressedRotatingFileHandler(log_file, maxBytes=10, backupCount=3)
        handler.setLevel(logging.DEBUG)

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="content that will be rotated", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.doRollover()
        handler.close()

        gz_files = [
            str(tmp_path / f)
            for f in os.listdir(tmp_path)
            if f.endswith(".gz")
        ]
        assert gz_files, "No .gz file was created"
        with gzip.open(gz_files[0], "rb") as f:
            content = f.read()
        assert b"content that will be rotated" in content

    def test_original_log_file_remains_writable(self, tmp_path):
        """After rollover the original log file is recreated and still writable."""
        log_file = str(tmp_path / "app.log")
        handler = CompressedRotatingFileHandler(log_file, maxBytes=10, backupCount=3)

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="initial content", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.doRollover()

        # Write a new record after rollover
        new_record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="post-rollover content", args=(), exc_info=None,
        )
        handler.emit(new_record)
        handler.close()

        with open(log_file) as f:
            assert "post-rollover content" in f.read()

    def test_backup_count_respected(self, tmp_path):
        """Backup count limits how many rotated .gz files are kept."""
        log_file = str(tmp_path / "app.log")
        backup_count = 2
        handler = CompressedRotatingFileHandler(
            log_file, maxBytes=5, backupCount=backup_count
        )

        for i in range(10):
            record = logging.LogRecord(
                name="test", level=logging.INFO,
                pathname="", lineno=0,
                msg=f"line {i} padding padding", args=(), exc_info=None,
            )
            handler.emit(record)

        handler.close()

        gz_files = [f for f in os.listdir(tmp_path) if f.endswith(".gz")]
        assert len(gz_files) <= backup_count


class TestCompressedTimedRotatingFileHandler:

    def test_rollover_produces_gz_file(self, tmp_path):
        """After a forced rollover, the rotated file has a .gz extension."""
        log_file = str(tmp_path / "timed.log")
        handler = CompressedTimedRotatingFileHandler(
            log_file, when="midnight", backupCount=3
        )
        handler.setLevel(logging.DEBUG)

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="timed rotation test", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.doRollover()
        handler.close()

        rotated_files = [f for f in os.listdir(tmp_path) if f != "timed.log"]
        assert any(f.endswith(".gz") for f in rotated_files), (
            f"Expected a .gz rotated file, got: {rotated_files}"
        )

    def test_rotated_gz_is_valid_gzip(self, tmp_path):
        """The .gz file produced by timed rollover is a valid gzip archive."""
        log_file = str(tmp_path / "timed.log")
        handler = CompressedTimedRotatingFileHandler(
            log_file, when="midnight", backupCount=3
        )

        record = logging.LogRecord(
            name="test", level=logging.INFO,
            pathname="", lineno=0,
            msg="timed content", args=(), exc_info=None,
        )
        handler.emit(record)
        handler.doRollover()
        handler.close()

        gz_files = [
            str(tmp_path / f) for f in os.listdir(tmp_path) if f.endswith(".gz")
        ]
        assert gz_files
        with gzip.open(gz_files[0], "rb") as f:
            content = f.read()
        assert b"timed content" in content
