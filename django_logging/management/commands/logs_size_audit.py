import logging
import os
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand

from django_logging.handlers import EmailHandler
from django_logging.management.commands.send_logs import Command as cmd
from django_logging.settings import settings_manager
from django_logging.utils.get_conf import (
    get_log_dir_size_limit,
    use_email_notifier_template,
)
from django_logging.utils.log_email_notifier.notifier import send_email_async

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Check the total size of the logs directory and send a warning if it
    exceeds the configured limit.

    This extended version also breaks down the size by category:
    - Active log files  (``<level>.log``)
    - Rotated log files (``<level>.log.N``, ``<level>.log.<date>``, etc.)
    - Archived files    (files inside the ``archive/`` subdirectory)
    - Compressed files  (``.gz`` variants of any of the above)

    Attributes:
        help (str): Brief description of the command's functionality.

    """

    help = (
        "Check the total size of the logs directory and send a warning "
        "if it exceeds the limit. Includes a breakdown by file category."
    )

    def handle(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        """Handles the command execution.

        Args:
            *args: Positional arguments passed to the command.
            **kwargs: Keyword arguments passed to the command.

        """
        log_dir = settings_manager.log_dir

        # Check if log directory exists
        if not os.path.exists(log_dir):
            self.stdout.write(self.style.ERROR(f"Log directory not found: {log_dir}"))
            logger.error("Log directory not found: %s", log_dir)
            return

        # pylint: disable=attribute-defined-outside-init
        self.size_limit: int = get_log_dir_size_limit()

        breakdown = self._categorize_files(log_dir)
        total_size = sum(s for _, s in breakdown.values())
        total_size_mb = float(f"{total_size / (1024 * 1024):.2f}")

        self._print_breakdown(breakdown, total_size_mb)
        logger.info("Total log directory size: %s MB", total_size_mb)

        if int(total_size_mb) >= self.size_limit:
            cmd.validate_email_settings()
            # Send warning email if total size exceeds the size limit
            self.send_warning_email(total_size_mb, breakdown)
            self.stdout.write(self.style.SUCCESS("Warning email sent successfully."))
            logger.info("Warning email sent successfully.")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Log directory size is under the limit: {total_size_mb} MB"
                )
            )
            logger.info("Log directory size is under the limit: %s MB", total_size_mb)

    def _categorize_files(self, log_dir: str) -> Dict[str, Tuple[List[str], int]]:
        """Walk *log_dir* and categorize files into active, rotated, archived,
        and compressed buckets.

        Returns:
            Dict mapping category name → (list of paths, total bytes).

        """
        from django_logging.constants.default_settings import DefaultLoggingSettings

        levels = [lvl.lower() for lvl in DefaultLoggingSettings().log_levels]
        active_names = {f"{lvl}.log" for lvl in levels}

        categories: Dict[str, List[str]] = {
            "active": [],
            "rotated": [],
            "archived": [],
            "compressed": [],
        }

        for root, _dirs, files in os.walk(log_dir):
            in_archive = "archive" in root.split(os.sep)
            for fname in files:
                fpath = os.path.join(root, fname)
                if in_archive:
                    categories["archived"].append(fpath)
                elif fname.endswith(".gz"):
                    categories["compressed"].append(fpath)
                elif fname in active_names:
                    categories["active"].append(fpath)
                else:
                    categories["rotated"].append(fpath)

        result: Dict[str, Tuple[List[str], int]] = {}
        for cat, paths in categories.items():
            size = sum(os.path.getsize(p) for p in paths)
            result[cat] = (paths, size)

        return result

    def _print_breakdown(
        self,
        breakdown: Dict[str, Tuple[List[str], int]],
        total_mb: float,
    ) -> None:
        self.stdout.write(self.style.HTTP_INFO("\nLog directory size breakdown:"))
        for category, (paths, size) in breakdown.items():
            size_mb = size / (1024 * 1024)
            self.stdout.write(
                f"  {category:<12} {len(paths):>4} file(s)   {size_mb:>8.2f} MB"
            )
        self.stdout.write(f"  {'TOTAL':<12}              {total_mb:>8.2f} MB\n")

    def send_warning_email(
        self,
        total_size_mb: float,
        breakdown: Dict[str, Tuple[List[str], int]],
    ) -> None:
        """Send an email warning to the admin about the log directory size.

        Args:
            total_size_mb: Total log directory size in MB.
            breakdown: Per-category size breakdown from ``_categorize_files``.

        """
        lines = [
            f"The size of the log files has exceeded {self.size_limit} MB.\n",
            f"Current size: {total_size_mb} MB\n\n",
            "Breakdown:\n",
        ]
        for category, (paths, size) in breakdown.items():
            size_mb = size / (1024 * 1024)
            lines.append(
                f"  {category:<12} {len(paths):>4} file(s)   {size_mb:.2f} MB\n"
            )

        message = "".join(lines)
        email_body = (
            EmailHandler.render_template(message)
            if use_email_notifier_template()
            else message
        )

        subject = "Logs Directory Size Warning"
        send_email_async(
            subject=subject,
            recipient_list=[settings.ADMIN_EMAIL],
            body=email_body,
        )
        logger.info(
            "Email has been sent to %s regarding log size warning.",
            settings.ADMIN_EMAIL,
        )
