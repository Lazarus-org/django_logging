import logging
from datetime import timedelta
from typing import Awaitable, Callable, Union

from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.core.management import call_command
from django.http import HttpRequest, HttpResponseBase
from django.utils.timezone import now

from django_logging.middleware.base import (  # pylint: disable=E0401, E0611
    BaseMiddleware,
)

logger = logging.getLogger(__name__)


class MonitorLogSizeMiddleware(BaseMiddleware):
    """Middleware that monitors the size of the log directory in both
    synchronous and asynchronous modes.

    This middleware checks if a week has passed since the last log size audit. If so, it runs
    the 'logs_size_audit' management command, which checks the log directory's total size.
    If the size exceeds a configured limit, a warning email is sent to the admin.

    Attributes:
    ----------
        get_response (Callable[[HttpRequest], Union[HttpResponseBase, Awaitable[HttpResponseBase]]]):
            The next middleware or view to be called.

    """

    # pylint: disable=useless-parent-delegation
    def __init__(
        self,
        get_response: Callable[
            [HttpRequest], Union[HttpResponseBase, Awaitable[HttpResponseBase]]
        ],
    ) -> None:
        """Initializes the middleware with the provided get_response callable.

        Args:
        ----
            get_response (callable): The next middleware or view to be called in the chain.

        """
        super().__init__(get_response)

    def __sync_call__(self, request: HttpRequest) -> HttpResponseBase:
        """Synchronous request processing.

        Args:
        ----
            request (HttpRequest): The current HTTP request being processed.

        Returns:
        -------
            HttpResponseBase: The HTTP response returned by the next middleware or view.

        """
        if self.should_run_task():
            self.run_log_size_check()
            cache.set("last_run_logs_size_audit", now(), timeout=None)

        return self.get_response(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        """Asynchronous request processing.

        Args:
        ----
            request (HttpRequest): The current HTTP request being processed.

        Returns:
        -------
            HttpResponseBase: The HTTP response returned by the next middleware or view.

        """
        if await sync_to_async(self.should_run_task)():
            await sync_to_async(self.run_log_size_check)()
            await sync_to_async(cache.set)(
                "last_run_logs_size_audit", now(), timeout=None
            )

        return await self.get_response(request)

    @staticmethod
    def should_run_task() -> bool:
        """Determines if a week has passed since the last log size audit.

        Returns:
        -------
            bool: True if a week has passed since the last audit, False otherwise.

        """
        last_run = cache.get("last_run_logs_size_audit")
        if last_run is None or now() - last_run > timedelta(weeks=1):
            return True

        return False

    def run_log_size_check(self) -> None:
        """Runs the 'logs_size_audit' management command to check the log
        directory size.

        If an error occurs during the execution of the command, it is
        logged.

        """
        logger.info("Running 'logs_size_audit' command...")
        try:
            call_command("logs_size_audit")
        except Exception as e:  # pylint: disable=W0718
            logger.error("Error running 'logs_size_audit' command: %s", e)
