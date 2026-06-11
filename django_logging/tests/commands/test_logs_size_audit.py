import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_logs_size_audit,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestCheckLogSizeCommand:
    """
    Test suite for the `check_log_size` management command.
    """

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    def test_command_log_directory_size_under_limit(
        self, mock_os_walk: MagicMock, temp_log_directory: str
    ) -> None:
        """
        Test that the command correctly handles the case when the log directory size is under the limit.

        This test verifies that the command calculates the log directory size correctly and does not send
        an email when the size is below the limit.

        Args:
            mock_os_walk (MagicMock): Mock for `os.walk`.
            temp_log_directory (str): Temporary log directory fixture.
        """
        # Mock the os.walk to return an empty directory
        mock_os_walk.return_value = [(temp_log_directory, [], [])]

        # Execute the command and capture the output
        out = StringIO()
        with patch("django.conf.settings.DJANGO_LOGGING", {"LOG_DIR_SIZE_LIMIT": 100}):
            call_command("logs_size_audit", stdout=out)

        assert "Log directory size is under the limit" in out.getvalue()

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    @patch("django_logging.management.commands.logs_size_audit.send_email_async")
    def test_command_log_directory_size_exceeds_limit(
        self,
        mock_send_email: MagicMock,
        mock_os_walk: MagicMock,
        temp_log_directory: str,
    ) -> None:
        """
        Test that the command sends a warning email when the log directory size exceeds the limit.

        This test verifies that the command calculates the log directory size correctly and sends
        an email notification when the size exceeds the limit.

        Args:
        ----
            mock_send_email (MagicMock): Mock for the `send_warning_email` method.
            mock_os_walk (MagicMock): Mock for `os.walk`.
            temp_log_directory (str): Temporary log directory fixture.
        """
        # Mock the os.walk to simulate a large directory
        mock_os_walk.return_value = [
            (temp_log_directory, [], ["log1.txt", "log2.txt"]),
        ]
        # Mock the file sizes to exceed the limit
        with patch("os.path.getsize", side_effect=[60 * 1024 * 1024, 50 * 1024 * 1024]):
            out = StringIO()
            with patch("django.conf.settings.ADMIN_EMAIL", "admin@example.com"):
                with patch("django_logging.management.commands.logs_size_audit.settings_manager.log_dir_size_limit", 100):
                    call_command("logs_size_audit", stdout=out)

        # Verify that the warning email was sent
        mock_send_email.assert_called_once()
        assert "Warning email sent successfully" in out.getvalue()

    @patch("os.path.exists", return_value=False)
    def test_command_log_directory_not_found(self, temp_log_directory: str) -> None:
        """
        Test that the command handles the case where the log directory does not exist.

        This test verifies that the command logs an error message and exits gracefully
        when the log directory is missing.

        Args:
        ----
            temp_log_directory (str): Temporary log directory fixture.
        """
        out = StringIO()
        call_command("logs_size_audit", stdout=out)

        assert "Log directory not found" in out.getvalue()

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    @patch("os.path.getsize", return_value=0)
    def test_breakdown_section_appears_in_output(
        self, mock_getsize: MagicMock, mock_os_walk: MagicMock, temp_log_directory: str
    ) -> None:
        """Output includes the per-category breakdown table."""
        mock_os_walk.return_value = [(temp_log_directory, [], [])]

        out = StringIO()
        with patch("django.conf.settings.DJANGO_LOGGING", {"LOG_DIR_SIZE_LIMIT": 1024}):
            call_command("logs_size_audit", stdout=out)

        output = out.getvalue()
        assert "active" in output
        assert "rotated" in output
        assert "archived" in output
        assert "compressed" in output

    @patch("os.path.exists", return_value=True)
    def test_categorize_files_separates_active_and_rotated(
        self, _mock_exists, tmp_path
    ) -> None:
        """_categorize_files correctly splits active, rotated, archived, and compressed."""
        from django.core.management import BaseCommand
        from django_logging.management.commands.logs_size_audit import Command

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Active
        (log_dir / "info.log").write_text("active")
        (log_dir / "error.log").write_text("active")
        # Rotated plain
        (log_dir / "info.log.1").write_text("rotated")
        # Rotated compressed
        (log_dir / "info.log.2.gz").write_bytes(b"fake gz")
        # Archived
        archive_dir = log_dir / "archive" / "2024-01-01_120000"
        archive_dir.mkdir(parents=True)
        (archive_dir / "debug.log.1").write_text("archived")

        cmd = Command()
        breakdown = cmd._categorize_files(str(log_dir))

        active_paths, _ = breakdown["active"]
        rotated_paths, _ = breakdown["rotated"]
        compressed_paths, _ = breakdown["compressed"]
        archived_paths, _ = breakdown["archived"]

        assert any("info.log" in p and not p.endswith(".1") and not p.endswith(".gz")
                   for p in active_paths)
        assert any("info.log.1" in p for p in rotated_paths)
        assert any("info.log.2.gz" in p for p in compressed_paths)
        assert any("debug.log.1" in p for p in archived_paths)

    @patch("os.path.exists", return_value=True)
    @patch("os.walk")
    @patch("django_logging.management.commands.logs_size_audit.send_email_async")
    def test_warning_email_body_includes_breakdown(
        self,
        mock_send_email: MagicMock,
        mock_os_walk: MagicMock,
        temp_log_directory: str,
    ) -> None:
        """The warning email body includes the per-category breakdown."""
        mock_os_walk.return_value = [
            (temp_log_directory, [], ["info.log", "info.log.1"]),
        ]
        with patch(
            "os.path.getsize",
            side_effect=[60 * 1024 * 1024, 50 * 1024 * 1024],
        ):
            out = StringIO()
            with patch("django.conf.settings.ADMIN_EMAIL", "admin@example.com"), \
                 patch(
                     "django_logging.management.commands.logs_size_audit.settings_manager.log_dir_size_limit",
                     100,
                 ):
                call_command("logs_size_audit", stdout=out)

        mock_send_email.assert_called_once()
        email_body = mock_send_email.call_args.kwargs.get("body", "") or \
                     mock_send_email.call_args[1].get("body", "")
        assert "active" in email_body or "rotated" in email_body or "Breakdown" in email_body
