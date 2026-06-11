"""Tests for the rotate_logs management command."""

import logging
import logging.handlers
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_rotate_logs,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestRotateLogsCommand:

    def test_rotates_rotating_file_handler(self, tmp_path):
        """doRollover is called on every RotatingFileHandler that is active."""
        log_file = str(tmp_path / "app.log")
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024, backupCount=3
        )
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            mock_rollover = MagicMock()
            with patch.object(handler, "doRollover", mock_rollover):
                out = StringIO()
                call_command("rotate_logs", stdout=out)

            mock_rollover.assert_called_once()
            assert "Rotated" in out.getvalue()
        finally:
            root_logger.removeHandler(handler)
            handler.close()

    def test_rotates_timed_rotating_file_handler(self, tmp_path):
        """doRollover is called on every TimedRotatingFileHandler that is active."""
        log_file = str(tmp_path / "timed.log")
        handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight")
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            mock_rollover = MagicMock()
            with patch.object(handler, "doRollover", mock_rollover):
                out = StringIO()
                call_command("rotate_logs", stdout=out)

            mock_rollover.assert_called_once()
        finally:
            root_logger.removeHandler(handler)
            handler.close()

    def test_skips_plain_file_handler(self, tmp_path):
        """Plain FileHandlers are reported as skipped, not rotated."""
        log_file = str(tmp_path / "plain.log")
        handler = logging.FileHandler(log_file)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        try:
            out = StringIO()
            call_command("rotate_logs", stdout=out)
            assert "Skipped" in out.getvalue()
        finally:
            root_logger.removeHandler(handler)
            handler.close()

    def test_no_rotating_handlers_warning(self):
        """When no rotating handlers exist a helpful warning is printed."""
        # Temporarily strip all handlers from root logger
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = []

        try:
            out = StringIO()
            call_command("rotate_logs", stdout=out)
            assert "No rotating handlers found" in out.getvalue()
        finally:
            root_logger.handlers = original_handlers

    def test_multiple_handlers_all_rotated(self, tmp_path):
        """All rotating handlers across multiple loggers are rotated."""
        handler_a = logging.handlers.RotatingFileHandler(
            str(tmp_path / "a.log"), maxBytes=512, backupCount=2
        )
        handler_b = logging.handlers.RotatingFileHandler(
            str(tmp_path / "b.log"), maxBytes=512, backupCount=2
        )
        root_logger = logging.getLogger()
        root_logger.addHandler(handler_a)
        root_logger.addHandler(handler_b)

        try:
            mock_a = MagicMock()
            mock_b = MagicMock()
            with (
                patch.object(handler_a, "doRollover", mock_a),
                patch.object(handler_b, "doRollover", mock_b),
            ):
                call_command("rotate_logs", stdout=StringIO())

            mock_a.assert_called_once()
            mock_b.assert_called_once()
        finally:
            root_logger.removeHandler(handler_a)
            root_logger.removeHandler(handler_b)
            handler_a.close()
            handler_b.close()
