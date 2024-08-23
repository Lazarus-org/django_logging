from unittest.mock import patch
from django_logging.validators.config_validators import (
    validate_directory,
    validate_log_levels,
    validate_format_string,
    validate_format_option,
    validate_boolean_setting,
    validate_date_format,
    validate_email_notifier,
)


def test_validate_directory_success():
    with patch("os.path.exists") as mock_exists, patch("os.mkdir") as mock_mkdir:
        mock_exists.return_value = False
        errors = validate_directory("new_dir", "test_directory")
        assert not errors
        mock_mkdir.assert_called_once()


def test_validate_directory_invalid_path():
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        errors = validate_directory(None, "test_directory")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E001_test_directory"

        errors = validate_directory("/path\to/file", "test_directory")
        assert len(errors) == 1
        assert errors[0].id == "django_logging.E002_test_directory"


def test_validate_directory_is_file():
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
            "The path specified in test_directory is not a directory." in errors[0].msg
        )
        assert "Ensure test_directory points to a valid directory." in errors[0].hint


def test_validate_log_levels_success():
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    errors = validate_log_levels(["DEBUG", "INFO"], "log_levels", valid_levels)
    assert not errors


def test_validate_log_levels_invalid_type():
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    errors = validate_log_levels("DEBUG, INFO", "log_levels", valid_levels)
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E004_log_levels"

    errors = validate_log_levels([], "log_levels", valid_levels)
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E005_log_levels"


def test_validate_format_string_success():
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    errors = validate_format_string(format_str, "log_format")
    assert not errors


def test_validate_format_string_invalid():
    format_str = "%(invalid)s"
    errors = validate_format_string(format_str, "log_format")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E011_log_format"

    format_str = tuple()  # invalid type
    errors = validate_format_string(format_str, "log_format")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E008_log_format"

    format_str = ""
    errors = validate_format_string(format_str, "log_format")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E009_log_format"


def test_validate_format_option_integer_success():
    format_option = 1
    errors = validate_format_option(format_option, "log_format_option")
    assert not errors


def test_validate_format_option_failure():
    format_option = 15
    errors = validate_format_option(format_option, "log_format_option")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E012_log_format_option"

    format_option = 1.5
    errors = validate_format_option(format_option, "log_format_option")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E013_log_format_option"


def test_validate_format_option_string_success():
    format_option = "%(asctime)s - %(message)s"
    errors = validate_format_option(format_option, "log_format_option")
    assert not errors


def test_validate_boolean_setting_success():
    errors = validate_boolean_setting(True, "boolean_setting")
    assert not errors


def test_validate_date_format_success():
    date_format = "%Y-%m-%d"
    errors = validate_date_format(date_format, "date_format")
    assert not errors


def test_validate_date_format_invalid_format():
    date_format = 1  # invalid type
    errors = validate_date_format(date_format, "date_format")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E015_date_format"

    date_format = "%invalid"
    errors = validate_date_format(date_format, "date_format")
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E016_date_format"


def test_validate_email_notifier_success():
    notifier_config = {
        "ENABLE": True,
        "LOG_FORMAT": "%(asctime)s - %(message)s",
        "NOTIFY_ERROR": True,
    }
    errors = validate_email_notifier(notifier_config)
    assert not errors


def test_validate_email_notifier_invalid_type():
    notifier_config = ["ENABLE", "LOG_FORMAT"]
    errors = validate_email_notifier(notifier_config)
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E017_LOG_EMAIL_NOTIFIER"

    notifier_config = {"ENABLE": "true", "LOG_FORMAT": "%(asctime)s - %(message)s"}
    errors = validate_email_notifier(notifier_config)
    assert len(errors) == 1
    assert errors[0].id == "django_logging.E018_LOG_EMAIL_NOTIFIER['ENABLE']"
