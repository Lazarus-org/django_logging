import json
import os
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
from django.core.management import call_command
from django.test import override_settings

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_generate_pretty_json,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestJsonReformatCommand:
    """
    Test suite for the Django management command that reformats JSON files in a log directory.

    This test suite verifies the functionality of the command, which searches for `.json` files,
    parses multiple JSON objects, and saves them in a 'pretty' subdirectory in a valid JSON array format.
    """

    @override_settings(DJANGO_LOGGING={"LOG_DIR": "/tmp/test_logs"})
    def test_command_successful_processing(
        self, temp_json_log_directory: str, settings: Any
    ) -> None:
        """
        Test the successful processing and pretty-printing of JSON files.

        This test verifies that the command:
        1. Processes JSON files in the 'json' directory.
        2. Writes pretty JSON arrays into the 'pretty' subdirectory.
        3. Logs the successful processing of files.

        Args:
            temp_json_log_directory (str): Path to the temporary log directory.
            settings (django.conf.Settings): Django settings.
        """
        settings.DJANGO_LOGGING["LOG_DIR"] = temp_json_log_directory

        out = StringIO()
        call_command("generate_pretty_json", stdout=out)

        # Check output
        assert "Processing file" in out.getvalue()
        assert (
            "reformatted and generated new pretty file successfully" in out.getvalue()
        )

        # Verify that the formatted JSON file exists in the pretty directory
        pretty_dir = os.path.join(
            settings.DJANGO_LOGGING.get("LOG_DIR"), "json", "pretty"
        )
        formatted_file = os.path.join(pretty_dir, "formatted_test.json")
        assert os.path.exists(formatted_file)

        # Load and verify the content of the generated pretty file
        with open(formatted_file) as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["key"] == "value"

    @override_settings(DJANGO_LOGGING={"LOG_DIR": "/non_existent_dir"})
    def test_command_file_not_found_error(self, settings: Any) -> None:
        """
        Test handling of FileNotFoundError when the log directory does not exist.

        This test checks that the command logs an error when it fails to find the specified log directory.

        Args:
            settings (django.conf.Settings): Django settings.
        """
        out = StringIO()
        call_command("generate_pretty_json", stdout=out)

        # Check if the command logs the directory not found error
        assert "does not exist." in out.getvalue()

    def test_command_invalid_json(self, temp_json_log_directory: str, settings: Any) -> None:
        """
        Test the command's handling of invalid JSON files.

        This test verifies that the command logs a JSONDecodeError when it encounters invalid JSON content.

        Args:
            temp_json_log_directory (str): Path to the temporary log directory.
            settings (django.conf.Settings): Django settings.
        """
        settings.DJANGO_LOGGING["LOG_DIR"] = temp_json_log_directory

        # Create a faulty JSON file with invalid syntax.
        faulty_json_file = Path(temp_json_log_directory) / "json" / "faulty.json"
        faulty_json_file.write_text(
            """
            {"key": "value", \n "key2" }
            
            """
        )  # Invalid JSON

        out = StringIO()
        call_command("generate_pretty_json", stdout=out)

        assert "faulty.json" in out.getvalue()
        assert 'Incomplete JSON object: {"key": "value","key2" }' in out.getvalue()
