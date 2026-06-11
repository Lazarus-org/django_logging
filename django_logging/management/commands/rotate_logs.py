"""Management command to manually trigger an immediate log rotation."""

import logging

# Make logging.handlers available at module level for isinstance checks above.
import logging.handlers  # noqa: E402  (placed after class to keep class readable)
from typing import Any, Dict, Tuple

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Trigger an immediate rotation of all active rotating log handlers.

    This is useful in deployment scripts — call it right after a deploy
    so the new process starts with fresh log files, and the old files
    are safely preserved as rotated backups.

    Only ``RotatingFileHandler`` and ``TimedRotatingFileHandler`` (and
    their compressed variants) support programmatic rotation.  Plain
    ``FileHandler`` instances are reported but skipped gracefully.

    """

    help = "Manually trigger an immediate rotation of all rotating log handlers."

    def handle(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        root_logger = logging.getLogger()
        all_loggers = [root_logger] + list(logging.Logger.manager.loggerDict.values())

        rotated: list = []
        skipped: list = []

        for lg in all_loggers:
            if not isinstance(lg, logging.Logger):
                continue
            for handler in lg.handlers:
                if isinstance(
                    handler,
                    (
                        logging.handlers.RotatingFileHandler,
                        logging.handlers.TimedRotatingFileHandler,
                    ),
                ):
                    handler.acquire()
                    try:
                        handler.doRollover()
                        rotated.append(getattr(handler, "baseFilename", str(handler)))
                    finally:
                        handler.release()
                elif isinstance(handler, logging.FileHandler):
                    skipped.append(getattr(handler, "baseFilename", str(handler)))

        if rotated:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Rotated {len(rotated)} handler(s):\n"
                    + "\n".join(f"  {f}" for f in rotated)
                )
            )
            logger.info("Manual log rotation triggered for: %s", rotated)
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No rotating handlers found. "
                    "Set LOG_ROTATION TYPE to 'size' or 'time' to enable rotation."
                )
            )

        if skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {len(skipped)} plain FileHandler(s) "
                    f"(rotation not supported):\n"
                    + "\n".join(f"  {f}" for f in skipped)
                )
            )
