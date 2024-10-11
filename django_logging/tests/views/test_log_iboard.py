import sys

import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from typing import Dict

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.views,
    pytest.mark.views_log_iboard,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


@pytest.mark.django_db
class TestLogiBoardView:
    """
    Test suite for the `LogiBoardView` class-based view.

    This test suite covers:
    - Access control for superuser and non-superuser.
    - Rendering the correct template for superuser.
    - Correct response and content type for non-superuser.

    Methods:
    - test_superuser_access: Ensures superusers can access the LogiBoard page.
    - test_non_superuser_access: Ensures non-superusers are forbidden from accessing the LogiBoard page.
    """

    def test_superuser_access(
        self, client: Client, setup_users: Dict[str, User]
    ) -> None:
        """
        Test that a superuser can access the `LogiBoardView` and the correct template is rendered.
        """
        client.login(username="admin", password="adminpassword")
        response = client.get(reverse("log-iboard"))
        assert response.status_code == 200, "Superuser should have access to the page."
        assert (
            "log_iboard.html" in response.template_name
        ), "Should render the correct template for superuser."

    def test_non_superuser_access(
        self, client: Client, setup_users: Dict[str, User]
    ) -> None:
        """
        Test that a non-superuser receives a 403 Forbidden response when accessing the `LogiBoardView`.
        """
        client.login(username="user", password="userpassword")
        response = client.get(reverse("log-iboard"))
        assert (
            response.status_code == 403
        ), "Non-superuser should not have access to the page."
        assert (
             "text/html" in response["Content-Type"]
        ), "'text/html' should be in Content type for forbidden access."
