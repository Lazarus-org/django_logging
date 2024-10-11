from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView


class LogiBoardView(TemplateView):
    """View to render the LogiBoard page for superusers.

    Non-superusers are denied access and shown an error response page
    with a 403 status code.

    """

    template_name = "log_iboard.html"

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Dict[str, Any]
    ) -> HttpResponse:
        """Handles GET requests. Renders the LogiBoard page for superusers,
        otherwise returns a 403 error response for non-superusers.

        Args:
            request (HttpRequest): The HTTP request object.
            *args (Any): Additional positional arguments.
            **kwargs (Dict[str, Any]): Additional keyword arguments.

        Returns:
            HttpResponse: The rendered LogiBoard page for superusers or an error response page for non-superusers.

        """
        if request.user.is_superuser:
            return super().get(request, *args, **kwargs)

        return render(
            request,
            "error_response.html",
            {
                "title": "Access Denied",
                "message": "You do not have permission to view this page.",
            },
            status=403,
        )
