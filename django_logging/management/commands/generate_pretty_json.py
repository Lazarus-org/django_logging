import json
import os
from typing import Dict, Tuple

from django.core.management.base import BaseCommand

from django_logging.settings import settings_manager
from django_logging.utils.command.process_file import process_files, setup_directories


class Command(BaseCommand):
    """A Django management command to find JSON files within a specified log
    directory and generate pretty JSON.

    The command looks for `.json` files inside the `json` subdirectory of the log directory, attempts to
    parse multiple JSON objects from a single file, and then formats them into a valid JSON array.

    The reformatted JSON content is saved in a `pretty` subdirectory with the prefix `formatted_`.

    """

    help = "Find JSON files in log directory and generates pretty JSON"

    def handle(self, *args: Tuple, **kwargs: Dict) -> None:
        """Main command handler. This method retrieves the log directory, sets
        up necessary directories, processes each `.json` file, and reformats
        the content.

        Args:
            *args: Additional positional arguments (not used).
            **kwargs: Additional keyword arguments (not used).

        """
        log_dir = settings_manager.log_dir

        try:
            json_dir, pretty_dir = setup_directories(log_dir, "json")
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(str(e)))
            return

        for file_path, filename in process_files(json_dir, ".json", self.reformat_json):
            self.stdout.write(self.style.NOTICE(f"Processing file: {file_path}"))

            new_file_path: str = os.path.join(pretty_dir, f"formatted_{filename}")
            self.reformat_json(file_path, new_file_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"File {filename} reformatted and generated new pretty file successfully."
                )
            )

    def reformat_json(self, file_path: str, new_file_path: str) -> None:
        """Parses multiple JSON objects from a file incrementally and writes
        them to a new file as a valid JSON array.

        Args:
            file_path (str): The path to the original JSON file.
            new_file_path (str): The path where the reformatted JSON file will be saved.

        """
        with (
            open(file_path, encoding="utf-8") as infile,
            open(new_file_path, "w", encoding="utf-8") as outfile,
        ):
            outfile.write("[\n")  # Start the JSON array
            first_object = True  # Flag to handle commas

            buffer = ""  # This will accumulate the JSON content

            for line in infile:
                line = line.strip()

                if not line:
                    continue  # Skip empty lines

                buffer += line

                # Try to parse the current buffer as a complete JSON object
                try:
                    json_object = json.loads(buffer)
                    json_line = json.dumps(json_object, indent=4)

                    if not first_object:
                        outfile.write(",\n")  # Add a comma before subsequent objects
                    outfile.write(json_line)

                    first_object = False
                    buffer = ""  # Clear the buffer after successful parsing
                except json.JSONDecodeError:
                    # Keep accumulating if it's not a complete JSON object yet
                    continue

            if buffer:
                # If any partial JSON is left in the buffer, log an error
                self.stdout.write(self.style.ERROR(f"Incomplete JSON object: {buffer}"))

            outfile.write("\n]")  # End the JSON array
