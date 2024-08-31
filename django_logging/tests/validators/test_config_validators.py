import sys
from unittest.mock import patch

import pytest

from django_logging.constants.config_types import LogLevels
from django_logging.validators.config_validators import (
    validate_boolean_setting,
    validate_date_format,
    validate_directory,
    validate_email_notifier,
    validate_format_option,
    validate_format_string,
    validate_log_levels,
)
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.validators,
    pytest.mark.config_validator,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestConfigValidator:

    def test_validate_directory_success(self) -> None:
        """
        Test the successful validation of a directory path.

        This test verifies that the `validate_directory` function correctly
        creates a new directory if it does not exist and does not return any
        errors when a valid directory path is provided.

        Mocks:
        ------
        - `os.path.exists` to simulate directory existence check.
        - `os.mkdir` to simulate directory creation.

        Asserts:
        -------
        - No errors are returned.
        - The directory creation function is called once.
        """
        with patch("os.path.exists") as mock_exists, patch("os.mkdir") as mock_mkdir:
            mock_exists.return_value = False
            errors = validate_directory("new_dir", "test_directory")
            assert not errors
            mock_mkdir.assert_called_once()

    def test_validate_directory_invalid_path(self) -> None:
        """
        Test validation of invalid directory paths.

        This test verifies that `validate_directory` returns appropriate errors
        when provided with invalid paths, such as `None` or invalid file paths.

        Mocks:
        ------
        - `os.path.exists` to simulate directory existence check.

        Asserts:
        -------
        - Appropriate errors are returned for invalid paths.
        """
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            errors = validate_directory(None, "test_directory")  # type: ignore
            assert len(errors) == 1
            assert errors[0].id == "django_logging.E001_test_directory"

            errors = validate_directory("/path\to/file", "test_directory")
            assert len(errors) == 1
            assert errors[0].id == "django_logging.E002_test_directory"

    def test_validate_directory_is_file(self) -> None:
        """
        Test validation when the path is a file, not a directory.

        This test verifies that `validate_directory` correctly identifies and
        returns an error when the specified path is a file instead of a directory.

        Mocks:
        ------
        - `os.path.isdir` to simulate directory check.
        - `os.path.isfile` to simulate file check.
        - `os.path.exists` to simulate path existence check.

        Asserts:
        -------
        - Appropriate error is returned indicating the path is not a directory.
        """
        file_path = "path/to/file.txt"

        with patch("os.path.isdir") as mock_isdir, patch(
            "os.path.isfile"
        ) as mock_isfile, patch("os.path.exists") as mock_exists:
            # Simulate that the path is a file, not a directory
            mock_isdir.return_value = False
            mock_isfile.return_value = True
            mock_exists.return_value = True

            errors = validate_directory(file_path, "test_directory")

            assert len(errors) == 1
            assert errors[0].id == "django_logging.E003_test_directory"
            assert (
                "The path specified in test_directory is not a directory."
                in errors[0].msg
            )
            assert (
                "Ensure test_directory points to a valid directory." in errors[0].hint
            )

    def test_validate_log_levels_success(self) -> None:
        """
        Test successful validation of log levels.

        This test verifies that `validate_log_levels` does not return any errors
        when provided with valid log levels.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for valid log levels.
        """
        valid_levels: LogLevels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        errors = validate_log_levels(["DEBUG", "INFO"], "log_levels", valid_levels)
        assert not errors

    def test_validate_log_levels_invalid_type(self) -> None:
        """
        Test validation of log levels with invalid types.

        This test verifies that `validate_log_levels` returns errors when provided
        with invalid log level types, such as a string or an empty list.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - Appropriate errors are returned for invalid log level types.
        """
        valid_levels: LogLevels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        errors = validate_log_levels("DEBUG, INFO", "log_levels", valid_levels)  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E004_log_levels"

        errors = validate_log_levels([], "log_levels", valid_levels)
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E005_log_levels"

    def test_validate_format_string_success(self) -> None:
        """
        Test successful validation of a log format string.

        This test verifies that `validate_format_string` does not return any errors
        when provided with a valid format string.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid format string.
        """
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        errors = validate_format_string(format_str, "log_format")
        assert not errors

    def test_validate_format_string_invalid(self) -> None:
        """
        Test validation of an invalid log format string.

        This test verifies that `validate_format_string` returns appropriate errors
        when provided with invalid format strings, such as incorrect placeholders
        or invalid types.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - Appropriate errors are returned for invalid format strings.
        """
        format_str = "%(invalid)s"
        errors = validate_format_string(format_str, "log_format")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E011_log_format"

        format_str = tuple()  # invalid type
        errors = validate_format_string(format_str, "log_format")  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E008_log_format"

        format_str = ""
        errors = validate_format_string(format_str, "log_format")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E009_log_format"

    def test_validate_format_option_integer_success(self) -> None:
        """
        Test successful validation of an integer format option.

        This test verifies that `validate_format_option` does not return any errors
        when provided with a valid integer format option.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid integer format option.
        """
        format_option = 1
        errors = validate_format_option(format_option, "log_format_option")
        assert not errors

    def test_validate_format_option_failure(self) -> None:
        """
        Test validation of invalid format options.

        This test verifies that `validate_format_option` returns appropriate errors
        when provided with invalid format options, such as integers that not in a valid
        range or non-integer values.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - Appropriate errors are returned for invalid format options.
        """
        format_option = 15
        errors = validate_format_option(format_option, "log_format_option")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E012_log_format_option"

        format_option = 1.5
        errors = validate_format_option(format_option, "log_format_option")  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E013_log_format_option"

    def test_validate_format_option_string_success(self) -> None:
        """
        Test successful validation of a string format option.

        This test verifies that `validate_format_option` does not return any errors
        when provided with a valid string format option.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid string format option.
        """
        format_option = "%(asctime)s - %(message)s"
        errors = validate_format_option(format_option, "log_format_option")
        assert not errors

    def test_validate_boolean_setting_success(self) -> None:
        """
        Test successful validation of a boolean setting.

        This test verifies that `validate_boolean_setting` does not return any errors
        when provided with a valid boolean setting.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid boolean setting.
        """
        errors = validate_boolean_setting(True, "boolean_setting")
        assert not errors

    def test_validate_date_format_success(self) -> None:
        """
        Test successful validation of a date format string.

        This test verifies that `validate_date_format` does not return any errors
        when provided with a valid date format string.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid date format string.
        """
        date_format = "%Y-%m-%d"
        errors = validate_date_format(date_format, "date_format")
        assert not errors

    def test_validate_date_format_invalid_format(self) -> None:
        """
        Test validation of invalid date format strings.

        This test verifies that `validate_date_format` returns appropriate errors
        when provided with invalid date format strings, such as incorrect types
        or invalid format patterns.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - Appropriate errors are returned for invalid date format strings.
        """
        date_format = 1  # invalid type
        errors = validate_date_format(date_format, "date_format")  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E015_date_format"

        date_format = "%Q"  # invalid format
        errors = validate_date_format(date_format, "date_format")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E016_date_format"

    def test_validate_email_notifier_success(self) -> None:
        """
        Test successful validation of email notifier configuration.

        This test verifies that `validate_email_notifier` does not return any errors
        when provided with a valid email notifier configuration.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - No errors are returned for a valid email notifier configuration.
        """
        notifier_config = {
            "ENABLE": True,
            "LOG_FORMAT": "%(asctime)s - %(message)s",
            "NOTIFY_ERROR": True,
        }
        errors = validate_email_notifier(notifier_config)
        assert not errors

    def test_validate_email_notifier_invalid_type(self) -> None:
        """
        Test validation of invalid email notifier configuration types.

        This test verifies that `validate_email_notifier` returns appropriate errors
        when provided with configurations that have incorrect types.

        Mocks:
        ------
        - None.

        Asserts:
        -------
        - Appropriate errors are returned for invalid configuration types.
        """
        notifier_config = ["ENABLE", "LOG_FORMAT"]
        errors = validate_email_notifier(notifier_config)  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E017_LOG_EMAIL_NOTIFIER"

        notifier_config = {"ENABLE": "true", "LOG_FORMAT": "%(asctime)s - %(message)s"}
        errors = validate_email_notifier(notifier_config)  # type: ignore
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E018_LOG_EMAIL_NOTIFIER['ENABLE']"
