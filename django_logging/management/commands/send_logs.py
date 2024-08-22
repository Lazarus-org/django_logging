import os
import shutil
import tempfile
import logging

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.conf import settings

from django_logging.validators.email_settings_validator import check_email_settings
from django_logging.constants import DefaultLoggingSettings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    A Django management command that zips the log directory and sends it to
    the specified email address.

    This command is used to send the log files to a specified email address.
    It zips the log directory, creates an email with the zipped file as an attachment,
    and sends it to the specified email address.
    """

    help = "Send log folder to the specified email address"

    def add_arguments(self, parser):
        """
        Add custom command arguments.

        Parameters:
            parser (ArgumentParser): The argument parser to add arguments to.
        """
        parser.add_argument(
            "email", type=str, help="The email address to send the logs to"
        )

    def handle(self, *args, **kwargs):
        """
        The main entry point for the command.

        Parameters:
            args (tuple): Positional arguments.
            kwargs (dict): Keyword arguments.
        """
        email = kwargs["email"]

        default_settings = DefaultLoggingSettings()

        log_dir = settings.DJANGO_LOGGING.get(
            "LOG_DIR", os.path.join(os.getcwd(), default_settings.log_dir)
        )

        if not os.path.exists(log_dir):
            self.stdout.write(
                self.style.ERROR(f'Log directory "{log_dir}" does not exist.')
            )
            logger.error(f'Log directory "{log_dir}" does not exist.')
            return

        self.validate_email_settings()

        # Create a temporary file to store the zipped logs
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            zip_path = f"{tmp_file.name}.zip"
            tmp_file.close()

            # Zip the log directory
            shutil.make_archive(tmp_file.name, "zip", log_dir)

        # Send the email with the zipped logs
        email_subject = "Log Files"
        email_body = "Please find the attached log files."
        email_message = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_file(zip_path)

        try:
            email_message.send()
            self.stdout.write(self.style.SUCCESS(f"Logs sent successfully to {email}."))
            logger.info(f"Logs sent successfully to {email}.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send logs: {e}"))
            logger.error(f"Failed to send logs: {e}")
        finally:
            # Clean up the temporary file if exists
            if os.path.exists(zip_path):
                os.remove(zip_path)
                logger.info("Temporary zip file cleaned up successfully.")

    def validate_email_settings(self):
        """
        Check if all required email settings are present in the settings file.

        Raises ImproperlyConfigured if any of the required email settings are missing.
        """
        errors = check_email_settings()
        if errors:
            logger.error(errors)
            raise ImproperlyConfigured(errors)
