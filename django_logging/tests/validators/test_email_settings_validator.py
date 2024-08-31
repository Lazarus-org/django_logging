import sys
from typing import Dict
from unittest.mock import patch

import pytest
from django.conf import settings

from django_logging.validators.email_settings_validator import check_email_settings
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.validators,
    pytest.mark.email_settings_validator,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestEmailSettingsValidator:

    def test_check_email_settings_all_present(self, mock_email_settings: Dict) -> None:
        """
        Test validation when all required email settings are present.

        This test verifies that `check_email_settings` does not return any errors
        when all required email settings are correctly configured.

        Mocks:
        ------
        - `settings.EMAIL_HOST` set to "smtp.example.com"
        - `settings.EMAIL_PORT` set to 587
        - `settings.EMAIL_HOST_USER` set to "user@example.com"
        - `settings.EMAIL_HOST_PASSWORD` set to "password"
        - `settings.DEFAULT_FROM_EMAIL` set to "from@example.com"
        - `settings.ADMIN_EMAIL` set to "to@example.com"

        Asserts:
        -------
        - No errors are returned when all required settings are present.
        """
        with patch.object(settings, "EMAIL_HOST", mock_email_settings["EMAIL_HOST"]):
            with patch.object(
                settings, "EMAIL_PORT", mock_email_settings["EMAIL_PORT"]
            ):
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

    def test_check_email_settings_missing_some(self, mock_email_settings: Dict) -> None:
        """
        Test validation when some required email settings are missing.

        This test verifies that `check_email_settings` returns an error when some
        required email settings are missing, specifically the `EMAIL_HOST_USER` setting.

        Mocks:
        ------
        - `settings.EMAIL_HOST` set to "smtp.example.com"
        - `settings.EMAIL_PORT` set to 587
        - `settings.EMAIL_HOST_USER` set to None (simulating missing setting)
        - `settings.EMAIL_HOST_PASSWORD` set to "password"
        - `settings.DEFAULT_FROM_EMAIL` set to "from@example.com"
        - `settings.ADMIN_EMAIL` set to "to@example.com"

        Asserts:
        -------
        - Exactly one error is returned indicating the missing `EMAIL_HOST_USER` setting.
        """
        with patch.object(settings, "EMAIL_HOST", mock_email_settings["EMAIL_HOST"]):
            with patch.object(
                settings, "EMAIL_PORT", mock_email_settings["EMAIL_PORT"]
            ):
                with patch.object(
                    settings, "EMAIL_HOST_USER", None  # Simulate missing setting
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
                                assert len(errors) == 1
                                assert (
                                    errors[0].msg
                                    == "Missing required email settings: EMAIL_HOST_USER"
                                )
                                assert errors[0].id == "django_logging.E021"

    def test_check_email_settings_all_missing(self) -> None:
        """
        Test validation when all required email settings are missing.

        This test verifies that `check_email_settings` returns an error when all
        required email settings are missing.

        Mocks:
        ------
        - `settings.EMAIL_HOST` set to None
        - `settings.EMAIL_PORT` set to None
        - `settings.EMAIL_HOST_USER` set to None
        - `settings.EMAIL_HOST_PASSWORD` set to None
        - `settings.DEFAULT_FROM_EMAIL` set to None
        - `settings.ADMIN_EMAIL` set to None

        Asserts:
        -------
        - Exactly one error is returned indicating all required email settings are missing.
        """
        with patch.object(settings, "EMAIL_HOST", None):
            with patch.object(settings, "EMAIL_PORT", None):
                with patch.object(settings, "EMAIL_HOST_USER", None):
                    with patch.object(settings, "EMAIL_HOST_PASSWORD", None):
                        with patch.object(settings, "DEFAULT_FROM_EMAIL", None):
                            with patch.object(settings, "ADMIN_EMAIL", None):
                                errors = check_email_settings()
                                assert len(errors) == 1
                                assert errors[0].msg.startswith(
                                    "Missing required email settings: EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,"
                                    " EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL, ADMIN_EMAIL"
                                )
                                assert errors[0].id == "django_logging.E021"
