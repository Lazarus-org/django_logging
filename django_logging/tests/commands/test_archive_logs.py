"""Tests for the archive_logs management command."""
import gzip
import os
import sys
import tarfile
import zipfile
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_archive_logs,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestArchiveLogsCommand:

    # ------------------------------------------------------------------
    # Basic archiving
    # ------------------------------------------------------------------

    def test_moves_rotated_files_to_archive_dir(self, log_dir_with_rotated_files):
        """Rotated files are moved into archive/<timestamp>/."""
        log_dir = log_dir_with_rotated_files
        out = StringIO()

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", stdout=out)

        output = out.getvalue()
        assert "Archived" in output

        # Archive directory should exist
        archive_root = os.path.join(log_dir, "archive")
        assert os.path.isdir(archive_root)
        timestamps = os.listdir(archive_root)
        assert len(timestamps) == 1

        archived_dir = os.path.join(archive_root, timestamps[0])
        archived_files = os.listdir(archived_dir)
        assert "debug.log.1" in archived_files
        assert "info.log.2024-01-15" in archived_files
        assert "error.log.1.gz" in archived_files

    def test_active_log_files_are_never_moved(self, log_dir_with_rotated_files):
        """Active <level>.log files must stay in place."""
        log_dir = log_dir_with_rotated_files
        active_levels = ("debug", "info", "warning", "error", "critical")

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", stdout=StringIO())

        for level in active_levels:
            assert os.path.exists(os.path.join(log_dir, f"{level}.log")), (
                f"{level}.log should not have been moved"
            )

    def test_no_rotated_files_prints_success(self, tmp_path):
        """When there are no rotated files the command exits cleanly."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "info.log").write_text("active\n")

        out = StringIO()
        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            str(log_dir),
        ):
            call_command("archive_logs", stdout=out)

        assert "No rotated log files found" in out.getvalue()

    def test_missing_log_directory(self, tmp_path):
        """A missing log dir prints an error and exits without crashing."""
        out = StringIO()
        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            str(tmp_path / "nonexistent"),
        ):
            call_command("archive_logs", stdout=out)

        assert "Log directory not found" in out.getvalue()

    # ------------------------------------------------------------------
    # --compress flag
    # ------------------------------------------------------------------

    def test_compress_flag_gzips_uncompressed_files(self, log_dir_with_rotated_files):
        """--compress creates .gz files for every uncompressed rotated file."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", compress=True, stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        timestamps = os.listdir(archive_root)
        archived_dir = os.path.join(archive_root, timestamps[0])
        archived_files = os.listdir(archived_dir)

        # Both plain rotated files should now be .gz
        assert "debug.log.1.gz" in archived_files
        assert "info.log.2024-01-15.gz" in archived_files
        # Already-compressed file should remain as-is
        assert "error.log.1.gz" in archived_files
        # Original plain rotated files must be gone
        assert "debug.log.1" not in archived_files
        assert "info.log.2024-01-15" not in archived_files

    def test_compress_flag_produces_valid_gzip(self, log_dir_with_rotated_files):
        """Compressed files produced by --compress must be valid gzip archives."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", compress=True, stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        archived_dir = os.path.join(archive_root, os.listdir(archive_root)[0])
        gz_path = os.path.join(archived_dir, "debug.log.1.gz")

        with gzip.open(gz_path, "rt") as f:
            content = f.read()
        assert "rotated debug 1" in content

    # ------------------------------------------------------------------
    # --bundle tar.gz
    # ------------------------------------------------------------------

    def test_bundle_targz_creates_archive_and_removes_dir(self, log_dir_with_rotated_files):
        """--bundle tar.gz creates a .tar.gz file and removes the directory."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", bundle="tar.gz", stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        entries = os.listdir(archive_root)
        # Directory should be gone; bundle file should exist
        assert len(entries) == 1
        assert entries[0].endswith(".tar.gz")

    def test_bundle_targz_is_valid_tar(self, log_dir_with_rotated_files):
        """The .tar.gz bundle is a valid tar archive containing the rotated files."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", bundle="tar.gz", stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        bundle_name = os.listdir(archive_root)[0]
        bundle_path = os.path.join(archive_root, bundle_name)

        with tarfile.open(bundle_path, "r:gz") as tar:
            names = tar.getnames()

        assert any("debug.log.1" in n for n in names)
        assert any("info.log.2024-01-15" in n for n in names)

    def test_bundle_zip_creates_archive_and_removes_dir(self, log_dir_with_rotated_files):
        """--bundle zip creates a .zip file and removes the directory."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", bundle="zip", stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        entries = os.listdir(archive_root)
        assert len(entries) == 1
        assert entries[0].endswith(".zip")

    def test_bundle_zip_is_valid_zip(self, log_dir_with_rotated_files):
        """The .zip bundle is a valid zip archive containing the rotated files."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", bundle="zip", stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        bundle_path = os.path.join(archive_root, os.listdir(archive_root)[0])

        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()

        assert any("debug.log.1" in n for n in names)
        assert any("info.log.2024-01-15" in n for n in names)

    # ------------------------------------------------------------------
    # --compress + --bundle combined
    # ------------------------------------------------------------------

    def test_compress_and_bundle_targz(self, log_dir_with_rotated_files):
        """--compress --bundle tar.gz gzips files first, then bundles."""
        log_dir = log_dir_with_rotated_files

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", compress=True, bundle="tar.gz", stdout=StringIO())

        archive_root = os.path.join(log_dir, "archive")
        bundle_path = os.path.join(archive_root, os.listdir(archive_root)[0])
        assert bundle_path.endswith(".tar.gz")

        with tarfile.open(bundle_path, "r:gz") as tar:
            names = tar.getnames()

        # Individual files should be .gz inside the bundle
        assert any("debug.log.1.gz" in n for n in names)
        assert any("info.log.2024-01-15.gz" in n for n in names)

    # ------------------------------------------------------------------
    # --dry-run flag
    # ------------------------------------------------------------------

    def test_dry_run_prints_plan_without_moving_files(self, log_dir_with_rotated_files):
        """--dry-run outputs what would happen but does not move any file."""
        log_dir = log_dir_with_rotated_files
        out = StringIO()

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", dry_run=True, stdout=out)

        output = out.getvalue()
        assert "[DRY RUN]" in output
        # No archive directory should have been created
        assert not os.path.isdir(os.path.join(log_dir, "archive"))

    def test_dry_run_with_compress_shows_gzip_annotation(self, log_dir_with_rotated_files):
        """--dry-run --compress annotates plain rotated files with (+ gzip)."""
        log_dir = log_dir_with_rotated_files
        out = StringIO()

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", compress=True, dry_run=True, stdout=out)

        assert "(+ gzip)" in out.getvalue()

    def test_dry_run_with_bundle_shows_bundle_path(self, log_dir_with_rotated_files):
        """--dry-run --bundle shows the bundle destination path."""
        log_dir = log_dir_with_rotated_files
        out = StringIO()

        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ):
            call_command("archive_logs", bundle="tar.gz", dry_run=True, stdout=out)

        output = out.getvalue()
        assert ".tar.gz" in output
        assert "[DRY RUN]" in output

    # ------------------------------------------------------------------
    # collect_rotated_files helper
    # ------------------------------------------------------------------

    def test_existing_archive_dir_is_not_re_archived(self, log_dir_with_rotated_files):
        """Files already inside archive/ are not collected again on a second run."""
        log_dir = log_dir_with_rotated_files

        # First run — moves rotated files into archive/
        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ), patch(
            "django_logging.management.commands.archive_logs.datetime",
        ) as mock_dt_first:
            mock_dt_first.now.return_value.strftime.return_value = "2024-01-01_100000"
            call_command("archive_logs", stdout=StringIO())

        # Create a fresh rotated file and run again with a different timestamp
        open(os.path.join(log_dir, "warning.log.1"), "w").close()

        out = StringIO()
        with patch(
            "django_logging.management.commands.archive_logs.settings_manager.log_dir",
            log_dir,
        ), patch(
            "django_logging.management.commands.archive_logs.datetime",
        ) as mock_dt_second:
            mock_dt_second.now.return_value.strftime.return_value = "2024-01-02_100000"
            call_command("archive_logs", stdout=out)

        output = out.getvalue()
        # Should have archived exactly the new file
        assert "warning.log.1" in output
        # Should have created a second timestamp subdirectory
        archive_dirs = os.listdir(os.path.join(log_dir, "archive"))
        assert len([d for d in archive_dirs if os.path.isdir(os.path.join(log_dir, "archive", d))]) == 2
