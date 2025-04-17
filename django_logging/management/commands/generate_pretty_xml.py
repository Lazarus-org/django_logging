import os
from typing import Any, Dict, Tuple

from django.core.management.base import BaseCommand

from django_logging.settings import settings_manager
from django_logging.utils.command.process_file import process_files, setup_directories


class Command(BaseCommand):
    """Command to find and reformat XML files in a specified directory.

    This command processes all XML files in the specified log directory, reformats
    them by wrapping their content in a <logs> element, and saves the reformatted
    files to a new directory. It handles parsing errors and logs the process steps.

    Attributes:
        help (str): A brief description of the command's functionality.

    """

    help = "Find and reformat XML files in a directory"

    def handle(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        """Handles the command execution.

        Args:
            *args: Positional arguments passed to the command.
            **kwargs: Keyword arguments passed to the command.

        """
        log_dir = settings_manager.log_dir

        try:
            xml_dir, pretty_dir = setup_directories(log_dir, "xml")
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            return

        for file_path, filename in process_files(
            xml_dir, ".xml", self.reformat_and_write_xml
        ):
            self.stdout.write(self.style.NOTICE(f"Processing file: {file_path}"))

            new_file_path = os.path.join(pretty_dir, f"formatted_{filename}")
            self.reformat_and_write_xml(file_path, new_file_path)
            self.stdout.write(
                self.style.SUCCESS(f"File {filename} reformatted successfully.")
            )

    def reformat_and_write_xml(self, file_path: str, new_file_path: str) -> None:
        """Reformats XML content by wrapping it in a <logs> element and writes
        it to a new file.

        Args:
            file_path (str): The path of the original XML file to be reformatted.
            new_file_path (str): The path where the reformatted XML file will be saved.

        """
        with (
            open(file_path, encoding="utf-8") as infile,
            open(new_file_path, "w", encoding="utf-8") as outfile,
        ):
            # Start the <logs> element
            outfile.write("<logs>\n")

            for line in infile:
                # Write each line to the formatted file
                if line.strip():  # Only process non-empty lines
                    outfile.write(line)

            # End the <logs> element
            outfile.write("</logs>\n")
