from typing import Dict

import pytest


@pytest.fixture
def mock_email_settings() -> Dict:
    """
    Fixture to mock Django email settings.

    Returns:
    --------
    dict: A dictionary containing mock email settings:
        - EMAIL_HOST: "smtp.example.com"
        - EMAIL_PORT: 587
        - EMAIL_HOST_USER: "user@example.com"
        - EMAIL_HOST_PASSWORD: "password"
        - DEFAULT_FROM_EMAIL: "from@example.com"
        - ADMIN_EMAIL: "to@example.com"
    """
    return {
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_PORT": 587,
        "EMAIL_HOST_USER": "user@example.com",
        "EMAIL_HOST_PASSWORD": "password",
        "DEFAULT_FROM_EMAIL": "from@example.com",
        "ADMIN_EMAIL": "to@example.com",
    }
