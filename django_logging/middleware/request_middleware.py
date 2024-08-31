import logging
from typing import Callable

from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    """Middleware to log information about each incoming request.

    This middleware logs the request path, the user making the request
    (if authenticated), and the user's IP address.

    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initializes the RequestLogMiddleware instance.

        Args:
            get_response: A callable that returns an HttpResponse object.

        """
        self.get_response = get_response
        user_model = get_user_model()
        self.username_field = user_model.USERNAME_FIELD

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Processes an incoming request and logs relevant information.

        Args:
            request: The incoming request object.

        Returns:
            The response object returned by the view function.

        """
        # Before view (and later middleware) are called.
        response = self.get_response(request)

        # After view is called.
        if hasattr(request, "user") and request.user.is_authenticated:
            user = getattr(request.user, self.username_field, "Anonymous")
        else:
            user = "Anonymous"

        # Get the user's IP address
        ip_address = self.get_ip_address(request)

        # Get the user agent
        user_agent = self.get_user_agent(request)

        # Attach IP and user agent to the request
        request.ip_address = ip_address
        request.browser_type = user_agent

        logger.info(
            "Request Info: (request_path: %s, user: %s,\n IP: %s, user_agent: %s)",
            request.path,
            user,
            ip_address,
            user_agent,
        )

        return response

    @staticmethod
    def get_ip_address(request: HttpRequest) -> str:
        """Retrieves the client's IP address from the request object."""
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip_address:
            ip_address = ip_address.split(",")[0]
        else:
            ip_address = request.META.get("LIMITED_ACCESS")
            if not ip_address:
                ip_address = request.META.get("REMOTE_ADDR")

        return ip_address

    @staticmethod
    def get_user_agent(request: HttpRequest) -> str:
        """Retrieves the client's user agent from the request object."""
        return request.META.get("HTTP_USER_AGENT", "Unknown User Agent")
