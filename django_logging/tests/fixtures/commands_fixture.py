from typing import Any

import pytest
from _pytest._py.path import LocalPath
from _pytest.tmpdir import TempPathFactory


@pytest.fixture
def temp_json_log_directory(tmpdir: Any) -> str:
    """
    Fixture to create a temporary log directory with sample JSON files for testing.

    Args:
        tmpdir (TempPathFactory): Temporary directory fixture provided by pytest.

    Returns:
        str: The path to the temporary log directory.
    """
    json_dir = tmpdir.mkdir("json")

    # Create a valid JSON file with multiple JSON objects.
    json_file = json_dir.join("test.json")
    json_file.write('{"key": "value"}\n{"key": "value2"}')

    return str(tmpdir)


@pytest.fixture
def temp_log_directory(tmpdir: LocalPath) -> str:
    """
    Fixture to create a temporary log directory for testing.

    Args:
        tmpdir (LocalPath): Temporary directory fixture provided by pytest.

    Returns:
        str: Path to the temporary log directory.
    """
    log_dir = tmpdir.mkdir("logs")
    return str(log_dir)


@pytest.fixture
def temp_xml_log_directory(tmpdir: Any) -> str:
    """
    Fixture to create a temporary log directory with sample XML files for testing.

    Args:
    ----
        tmpdir (TempPathFactory): Temporary directory fixture provided by pytest.

    Returns:
    -------
        str: The path to the temporary log directory.
    """
    # Create the directory structure for logs/xml and logs/pretty
    xml_dir = tmpdir.mkdir("xml")

    # Create a valid XML file for testing
    xml_file = xml_dir.join("test.xml")
    xml_file.write("<log><entry>Test Entry</entry></log>")

    return str(tmpdir)
