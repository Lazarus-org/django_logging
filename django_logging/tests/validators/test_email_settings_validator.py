import pytest
from unittest.mock import patch
from django.conf import settings

from django_logging.validators.email_settings_validator import check_email_settings


# Mock required email settings for testing
@pytest.fixture
def mock_email_settings():
    """Fixture to mock Django email settings."""
    return {
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_PORT": 587,
        "EMAIL_HOST_USER": "user@example.com",
        "EMAIL_HOST_PASSWORD": "password",
        "DEFAULT_FROM_EMAIL": "from@example.com",
        "ADMIN_EMAIL": "to@example.com",
    }


def test_check_email_settings_all_present(mock_email_settings):
    """Test when all required email settings are present."""
    with patch.object(settings, "EMAIL_HOST", mock_email_settings["EMAIL_HOST"]):
        with patch.object(settings, "EMAIL_PORT", mock_email_settings["EMAIL_PORT"]):
            with patch.object(
                settings, "EMAIL_HOST_USER", mock_email_settings["EMAIL_HOST_USER"]
            ):
                with patch.object(
                    settings,
                    "EMAIL_HOST_PASSWORD",
                    mock_email_settings["EMAIL_HOST_PASSWORD"],
                ):
                    with patch.object(
                        settings,
                        "DEFAULT_FROM_EMAIL",
                        mock_email_settings["DEFAULT_FROM_EMAIL"],
                    ):
                        with patch.object(
                                settings,
                                "ADMIN_EMAIL",
                                mock_email_settings["ADMIN_EMAIL"],
                        ):
                            errors = check_email_settings()
                            assert not errors  # No errors should be present


def test_check_email_settings_missing_some(mock_email_settings):
    """Test when some required email settings are missing."""
    with patch.object(settings, "EMAIL_HOST", mock_email_settings["EMAIL_HOST"]):
        with patch.object(settings, "EMAIL_PORT", mock_email_settings["EMAIL_PORT"]):
            with patch.object(
                settings, "EMAIL_HOST_USER", None
            ):  # Simulate missing setting
                with patch.object(
                    settings,
                    "EMAIL_HOST_PASSWORD",
                    mock_email_settings["EMAIL_HOST_PASSWORD"],
                ):
                    with patch.object(
                        settings,
                        "DEFAULT_FROM_EMAIL",
                        mock_email_settings["DEFAULT_FROM_EMAIL"],
                    ):
                        with patch.object(
                                settings,
                                "ADMIN_EMAIL",
                                mock_email_settings["ADMIN_EMAIL"],
                        ):
                            errors = check_email_settings()
                            assert len(errors) == 1
                            assert (
                                errors[0].msg
                                == "Missing required email settings: EMAIL_HOST_USER"
                            )
                            assert errors[0].id == "django_logging.E021"


def test_check_email_settings_all_missing():
    """Test when all required email settings are missing."""
    with patch.object(settings, "EMAIL_HOST", None):
        with patch.object(settings, "EMAIL_PORT", None):
            with patch.object(settings, "EMAIL_HOST_USER", None):
                with patch.object(settings, "EMAIL_HOST_PASSWORD", None):
                    with patch.object(settings, "DEFAULT_FROM_EMAIL", None):
                        with patch.object(settings, "ADMIN_EMAIL", None):
                            errors = check_email_settings()
                            assert len(errors) == 1
                            assert errors[0].msg.startswith(
                                'Missing required email settings: EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,'
                                ' EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL, ADMIN_EMAIL'
                            )
                            assert errors[0].id == "django_logging.E021"
