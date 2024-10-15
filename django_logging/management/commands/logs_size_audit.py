import logging
import os
from typing import Any, Dict, Tuple

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
    """Command to check the total size of the logs directory and send a warning
    if it exceeds the limit.

    This command calculates the total size of the log directory and sends an email notification
    to the admin if the size exceeds the configured limit.

    Attributes:
        help (str): A brief description of the command's functionality.

    """

    help = "Check the total size of the logs directory and send a warning if it exceeds the limit"

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

        # Calculate the total size of the log directory
        total_size = self.get_directory_size(log_dir)
        total_size_mb = float(f"{total_size / (1024 * 1024):.2f}")

        logger.info("Total log directory size: %s MB", total_size_mb)

        if int(total_size_mb) >= self.size_limit:
            cmd.validate_email_settings()
            # Send warning email if total size exceeds the size limit
            self.send_warning_email(total_size_mb)
            self.stdout.write(self.style.SUCCESS("Warning email sent successfully."))
            logger.info("Warning email sent successfully.")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Log directory size is under the limit: {total_size_mb} MB"
                )
            )
            logger.info("Log directory size is under the limit: %s MB", total_size_mb)

    # pylint: disable=unused-variable
    def get_directory_size(self, dir_path: str) -> int:
        """Calculate the total size of all files in the directory.

        Args:
            dir_path (str): The path of the directory to calculate size for.

        Returns:
            int: The total size of the directory in bytes.

        """
        total_size = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)

        return total_size

    def send_warning_email(self, total_size_mb: float) -> None:
        """Send an email warning to the admin about the log directory size.

        Args:
            total_size_mb (int): The total size of the log directory in Megabytes.

        """

        subject = "Logs Directory Size Warning"
        recipient_list = [settings.ADMIN_EMAIL]
        message = (
            f"The size of the log files has exceeded {self.size_limit} MB.\n\n"
            f"Current size: {total_size_mb} MB\n"
        )

        email_body = message

        if use_email_notifier_template():
            email_body = EmailHandler.render_template(message)

        send_email_async(
            subject=subject, recipient_list=recipient_list, body=email_body
        )
        logger.info(
            "Email has been sent to %s regarding log size warning.",
            settings.ADMIN_EMAIL,
        )
