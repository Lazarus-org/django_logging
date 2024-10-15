from typing import Dict

import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def setup_users() -> Dict[str, User]:
    """
    Fixture to create a superuser and a normal user for testing purposes.
    Returns a dictionary with `superuser` and `non_superuser` keys.
    """
    superuser = User.objects.create_superuser(
        username="admin", password="adminpassword", email="admin@example.com"
    )
    non_superuser = User.objects.create_user(
        username="user", password="userpassword", email="user@example.com"
    )
    return {"superuser": superuser, "non_superuser": non_superuser}


@pytest.fixture
def client() -> Client:
    """
    Fixture to provide a test client.
    """
    return Client()
