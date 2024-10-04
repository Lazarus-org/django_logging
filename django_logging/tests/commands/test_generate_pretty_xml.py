import os
import sys
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.test import override_settings

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.commands,
    pytest.mark.commands_generate_pretty_xml,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestGeneratePrettyXMLCommand:
    """
    Test suite for the `generate_pretty_xml` management command.

    This test suite verifies the functionality of the command, which searches for `.xml` files,
    reformats them by wrapping their content in a <logs> element, and saves them in a 'pretty' subdirectory.
    """

    @override_settings(DJANGO_LOGGING={"LOG_DIR": "/tmp/test_logs"})
    def test_command_successful_processing(
            self, temp_xml_log_directory: str, settings: Any
    ) -> None:
        """
        Test the successful processing and reformatting of XML files.

        This test verifies that the command:
        1. Processes XML files in the 'xml' directory.
        2. Writes reformatted XML files into the 'pretty' subdirectory.
        3. Logs the successful processing of files.

        Args:
        ----
            temp_xml_log_directory (str): Path to the temporary log directory.
            settings (django.conf.Settings): Django settings.
        """
        # Update the settings to point to the temp log directory
        settings.DJANGO_LOGGING["LOG_DIR"] = temp_xml_log_directory

        out = StringIO()
        call_command("generate_pretty_xml", stdout=out)

        # Check command output for success message
        assert "Processing file" in out.getvalue()
        assert "File test.xml reformatted successfully." in out.getvalue()

        # Verify that the reformatted XML file exists in the pretty directory
        pretty_dir = os.path.join(
            settings.DJANGO_LOGGING["LOG_DIR"], "xml", "pretty"
        )
        formatted_file = os.path.join(pretty_dir, "formatted_test.xml")
        assert os.path.exists(formatted_file), "Reformatted file was not created."

        # Check the content of the generated pretty XML file
        with open(formatted_file) as f:
            content = f.read()
            assert "<logs>" in content
            assert "<entry>Test Entry</entry>" in content
            assert "</logs>" in content

    @override_settings(DJANGO_LOGGING={"LOG_DIR": "/non_existent_dir"})
    def test_command_directory_not_found(self, settings: Any) -> None:
        """
        Test that the command handles the case when the XML directory is missing.

        This test checks that the command outputs an appropriate error message when the directory does not exist.

        Args:
        ----
            settings (django.conf.Settings): Django settings.
        """
        out = StringIO()
        call_command("generate_pretty_xml", stdout=out)

        # Verify error output
        assert "does not exist." in out.getvalue()
