"""Management command to archive and compress rotated log files."""

import gzip
import logging
import os
import shutil
import tarfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandParser

from django_logging.settings import settings_manager

logger = logging.getLogger(__name__)

# Supported directory bundle formats
BUNDLE_FORMATS = ("tar.gz", "zip")


class Command(BaseCommand):
    """Archive rotated log files into a timestamped subdirectory.

    By default this command:
    1. Scans the log directory for rotated files (anything that is NOT a
       plain ``<level>.log`` active log file, e.g. ``info.log.1``,
       ``debug.log.2024-01-15``, ``warning.log.1.gz``).
    2. Moves them into ``<LOG_DIR>/archive/<YYYY-MM-DD_HHMMSS>/``.
    3. Optionally compresses individual uncompressed files before moving
       (``--compress``).
    4. Optionally bundles the entire archive directory into a single
       ``tar.gz`` or ``zip`` file and removes the directory
       (``--bundle tar.gz`` or ``--bundle zip``).

    The active ``.log`` files are never touched.

    """

    help = (
        "Move rotated log files into a timestamped archive subdirectory, "
        "optionally compressing individual files (--compress) or bundling "
        "the whole archive into a single tar.gz / zip file (--bundle)."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--compress",
            action="store_true",
            default=False,
            help="Gzip-compress each uncompressed rotated file before archiving.",
        )
        parser.add_argument(
            "--bundle",
            choices=BUNDLE_FORMATS,
            default=None,
            metavar="FORMAT",
            help=(
                "After archiving, bundle the entire archive directory into a "
                "single compressed file and remove the directory. "
                f"Supported formats: {', '.join(BUNDLE_FORMATS)}."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print what would happen without touching any files.",
        )

    def handle(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        log_dir: str = settings_manager.log_dir
        compress: bool = kwargs["compress"]
        bundle: Optional[str] = kwargs["bundle"]
        dry_run: bool = kwargs["dry_run"]

        if not os.path.isdir(log_dir):
            self.stdout.write(self.style.ERROR(f"Log directory not found: {log_dir}"))
            return

        rotated_files = self._collect_rotated_files(log_dir)

        if not rotated_files:
            self.stdout.write(self.style.SUCCESS("No rotated log files found."))
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        archive_dir = os.path.join(log_dir, "archive", timestamp)
        bundle_path = f"{archive_dir}.{bundle}" if bundle else None

        if dry_run:
            self._print_dry_run(
                rotated_files, archive_dir, compress, bundle, bundle_path
            )
            return

        # --- Step 1: move (and optionally compress) individual files ---
        archived = self._move_files(rotated_files, archive_dir, compress)

        self.stdout.write(
            self.style.SUCCESS(
                f"Archived {len(archived)} file(s) to {archive_dir}:\n"
                + "\n".join(f"  {f}" for f in archived)
            )
        )
        logger.info(
            "Archived %d rotated log file(s) to %s.", len(archived), archive_dir
        )

        # --- Step 2: bundle the directory if requested ---
        if bundle:
            self._bundle_directory(archive_dir, bundle_path, bundle)

    # ------------------------------------------------------------------
    # File collection
    # ------------------------------------------------------------------

    def _collect_rotated_files(self, log_dir: str) -> List[str]:
        """Walk *log_dir* and return paths of rotated (non-active) log files.

        Active files match exactly ``<level>.log`` (e.g. ``debug.log``).
        Everything else (``debug.log.1``, ``info.log.gz``,
        ``error.log.2024-03-01``, etc.) is considered rotated.

        """
        from django_logging.constants.default_settings import DefaultLoggingSettings

        levels = [lvl.lower() for lvl in DefaultLoggingSettings().log_levels]
        active_names = {f"{lvl}.log" for lvl in levels}

        rotated: List[str] = []
        for root, _dirs, files in os.walk(log_dir):
            # Never descend into existing archive subdirectories
            if "archive" in root.split(os.sep):
                continue
            for fname in files:
                if fname not in active_names:
                    rotated.append(os.path.join(root, fname))

        return sorted(rotated)

    # ------------------------------------------------------------------
    # Move / compress individual files
    # ------------------------------------------------------------------

    def _move_files(
        self, rotated_files: List[str], archive_dir: str, compress: bool
    ) -> List[str]:
        """Move *rotated_files* into *archive_dir*, gzipping if requested."""
        os.makedirs(archive_dir, exist_ok=True)
        archived: List[str] = []

        for src in rotated_files:
            filename = os.path.basename(src)

            if compress and not src.endswith(".gz"):
                dest = os.path.join(archive_dir, filename + ".gz")
                with open(src, "rb") as f_in, gzip.open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(src)
            else:
                dest = os.path.join(archive_dir, filename)
                shutil.move(src, dest)

            archived.append(dest)

        return archived

    # ------------------------------------------------------------------
    # Directory bundling
    # ------------------------------------------------------------------

    def _bundle_directory(self, archive_dir: str, bundle_path: str, fmt: str) -> None:
        """Compress *archive_dir* into *bundle_path* and remove the directory.

        Args:
            archive_dir: The directory to bundle.
            bundle_path: Full destination path for the bundle file.
            fmt: One of ``"tar.gz"`` or ``"zip"``.

        """
        if fmt == "tar.gz":
            self._make_targz(archive_dir, bundle_path)
        elif fmt == "zip":
            self._make_zip(archive_dir, bundle_path)

        # Remove the now-bundled directory
        shutil.rmtree(archive_dir)

        size_mb = os.path.getsize(bundle_path) / (1024 * 1024)
        self.stdout.write(
            self.style.SUCCESS(
                f"Bundled archive directory into {bundle_path} "
                f"({size_mb:.2f} MB) and removed the source directory."
            )
        )
        logger.info(
            "Archive directory bundled into %s (%.2f MB).", bundle_path, size_mb
        )

    @staticmethod
    def _make_targz(source_dir: str, dest_path: str) -> None:
        """Create a gzip-compressed tar archive of *source_dir* at
        *dest_path*."""
        with tarfile.open(dest_path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    @staticmethod
    def _make_zip(source_dir: str, dest_path: str) -> None:
        """Create a zip archive of *source_dir* at *dest_path*."""
        with zipfile.ZipFile(dest_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(source_dir):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    arcname = os.path.relpath(
                        full_path, start=os.path.dirname(source_dir)
                    )
                    zf.write(full_path, arcname)

    # ------------------------------------------------------------------
    # Dry-run output
    # ------------------------------------------------------------------

    def _print_dry_run(
        self,
        rotated_files: List[str],
        archive_dir: str,
        compress: bool,
        bundle: Optional[str],
        bundle_path: Optional[str],
    ) -> None:
        self.stdout.write(
            self.style.WARNING(
                f"[DRY RUN] Would archive {len(rotated_files)} file(s) "
                f"to {archive_dir}:"
            )
        )
        for f in rotated_files:
            action = " (+ gzip)" if compress and not f.endswith(".gz") else ""
            self.stdout.write(f"  {f}{action}")

        if bundle:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would then bundle the directory into: {bundle_path}\n"
                    f"          and remove: {archive_dir}"
                )
            )
