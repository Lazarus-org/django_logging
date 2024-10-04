import asyncio
import logging
from time import perf_counter
from typing import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Union,
)
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connection
from django.http import HttpRequest, HttpResponseBase, StreamingHttpResponse

from django_logging.contextvar import manager
from django_logging.middleware.base import BaseMiddleware
from django_logging.utils.get_conf import is_log_sql_queries_enabled
from django_logging.utils.time import format_elapsed_time

logger = logging.getLogger(__name__)


class RequestLogMiddleware(BaseMiddleware):
    """Middleware to log information about each incoming request, handling both
    synchronous and asynchronous requests.

    Attributes:
        sync_capable (bool): Indicates if the middleware can handle synchronous requests.
        async_capable (bool): Indicates if the middleware can handle asynchronous requests.
        get_response (Callable): The next middleware or view to be called in the request/response cycle.
        async_mode (bool): Whether the get_response function is asynchronous.
        username_field (str): The field representing the username in the User model.

    """

    sync_capable: bool = True
    async_capable: bool = True

    def __init__(
        self,
        get_response: Callable[
            [HttpRequest], Union[HttpResponseBase, Awaitable[HttpResponseBase]]
        ],
    ) -> None:
        """Initializes the RequestLogMiddleware instance.

        Args:
            get_response (Callable): The next middleware or view to handle the request.

        """
        super().__init__(get_response)
        self.log_sql = is_log_sql_queries_enabled()

        user_model = get_user_model()
        self.username_field = user_model.USERNAME_FIELD  # type: ignore

    def __sync_call__(self, request: HttpRequest) -> HttpResponseBase:
        """Handles the request synchronously.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            HttpResponseBase: The synchronous HTTP response.

        """
        request_id = self._prepare_request(request)
        start_time = perf_counter()

        if self.log_sql:
            self.initial_queries = len(connection.queries)  # pylint: disable=W0201

        response = self.get_response(request)

        if isinstance(response, StreamingHttpResponse):
            response.streaming_content = self._sync_streaming_wrapper(
                response.streaming_content, request_id
            )

        self._finalize_request(request, response, start_time)

        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        """Handles the request asynchronously.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            HttpResponseBase: The asynchronous HTTP response.

        """
        request_id = self._prepare_request(request)
        start_time = perf_counter()

        if self.log_sql:
            self.initial_queries = len(connection.queries)  # pylint: disable=W0201

        try:
            response = await self.get_response(request)
        except asyncio.CancelledError:
            logger.warning("Request was cancelled: request_id=%s", request_id)
            raise

        if isinstance(response, StreamingHttpResponse):
            response.streaming_content = self._async_streaming_wrapper(
                response.streaming_content, request_id
            )

        await sync_to_async(self._finalize_request, thread_sensitive=False)(
            request, response, start_time
        )

        return response

    def _prepare_request(self, request: HttpRequest) -> str:
        """Prepares the request for processing by generating a request ID and
        logging initial details.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The generated or retrieved request ID.

        """
        request_id = self.get_request_id(request) or str(uuid4())

        ip_address = self.get_ip_address(request)
        user_agent = self.get_user_agent(request)

        self.context = {  # pylint: disable=W0201
            "request_id": request_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        manager.bind(**self.context)

        log_message = (
            f"REQUEST STARTED:\n\tmethod={request.method}\n\t"
            f"path={request.path}\n\t"
            f"query_params={request.GET.dict() or None}\n\t"
            f"referrer={request.META.get('HTTP_REFERER', 'None')}\n"
        )
        logger.info(log_message)

        return request_id

    def _finalize_request(
        self,
        request: HttpRequest,
        response: Union[HttpResponseBase, Awaitable[HttpResponseBase]],
        start_time: float,
    ) -> None:
        """Finalizes the request by logging the response details and the time
        taken to process the request.

        Args:
            request (HttpRequest): The incoming HTTP request.
            response (HttpResponseBase): The outgoing HTTP response.
            start_time (float): The time when the request started.

        """
        user = self.get_user(request)
        status_code = response.status_code
        content_type = response.get("Content-Type", "Unknown")
        response_time = format_elapsed_time(perf_counter() - start_time)

        sql_log = self._log_sql_queries(self.initial_queries) if self.log_sql else ""

        logger.info(
            "REQUEST FINISHED:\n\tuser=%s\n\tstatus_code=%d"
            "\n\tcontent_type=[%s]\n\tresponse_time=[%s]\n\t%s",
            user,
            status_code,
            content_type,
            response_time,
            sql_log,
        )
        manager.clear()

    def _sync_streaming_wrapper(
        self, streaming_content: Generator[bytes, None, None], request_id: str
    ) -> Generator[bytes, None, None]:
        """Wraps synchronous streaming content for logging.

        Args:
            streaming_content (Generator[bytes, None, None]): The streaming content to be wrapped.
            request_id (str): The request ID for the current request.

        Returns:
            Generator[bytes, None, None]: The wrapped streaming content.

        """
        logger.info("Streaming started: request_id=%s", request_id)
        try:
            yield from streaming_content
        except Exception:
            logger.exception("Streaming failed: request_id=%s", request_id)
            raise

        logger.info("Streaming finished: request_id=%s", request_id)

    async def _async_streaming_wrapper(
        self, streaming_content: AsyncGenerator[bytes, None], request_id: str
    ) -> AsyncGenerator[bytes, None]:
        """Wraps asynchronous streaming content for logging.

        Args:
            streaming_content (AsyncGenerator[bytes, None]): The asynchronous streaming content to be wrapped.
            request_id (str): The request ID for the current request.

        Returns:
            AsyncGenerator[bytes, None]: The wrapped streaming content.

        """
        logger.info("Streaming started: request_id=%s", request_id)
        try:
            async for chunk in streaming_content:
                yield chunk
        except asyncio.CancelledError:
            logger.warning("Streaming was cancelled: request_id=%s", request_id)
            raise
        except Exception:
            logger.exception("Streaming failed: request_id=%s", request_id)
            raise

        logger.info("Streaming finished: request_id=%s", request_id)

    def get_user(self, request: HttpRequest) -> str:
        """Retrieves the username and ID of the authenticated user or returns
        'Anonymous' if the user is unauthenticated.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The username and ID of the authenticated user, or 'Anonymous'.

        """
        if hasattr(request, "user") and request.user.is_authenticated:
            username = getattr(request.user, self.username_field, "Anonymous")
            return f"[{username} (ID:{request.user.pk})]"
        return "Anonymous"

    @staticmethod
    def get_ip_address(request: HttpRequest) -> str:
        """Retrieves the client's IP address from the request. Caches the
        result for reuse.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The client's IP address.

        """
        # Return the cached IP address if it exists
        if hasattr(request, "ip_address"):
            return request.ip_address

        ip_address = request.META.get("HTTP_X_FORWARDED_FOR")

        if ip_address:
            # Split on commas and strip whitespace from each part
            ip_address_list = [ip.strip() for ip in ip_address.split(",")]
            # Use the first valid IP in the list
            if ip_address_list:
                return ip_address_list[0]

        # Fallback to REMOTE_ADDR if no valid X-Forwarded-For header
        return request.META.get("REMOTE_ADDR", "Unknown IP")

    @staticmethod
    def get_user_agent(request: HttpRequest) -> str:
        """Retrieves the client's user agent from the request.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            str: The client's user agent.

        """
        return request.META.get("HTTP_USER_AGENT", "Unknown User Agent")

    @staticmethod
    def get_request_id(request: HttpRequest) -> Optional[str]:
        """Retrieves the request ID from the headers or meta data.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            request_id(Optional[str]): the request_id of request object.

        """
        request_id = None
        if hasattr(request, "headers"):
            request_id = request.headers.get("x-request-id")

        return request.META.get("HTTP_X_REQUEST_ID") or request_id

    def _log_sql_queries(
        self, initial_queries: int, test_queries: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """Logs the SQL queries executed during the request or uses test
        queries for testing purposes.

        Args:
            initial_queries (int): The count of queries before the request started.
            test_queries (Optional[List[Dict]]): A list of test queries to simulate the real query logs.
                This is used for testing purposes to avoid modifying or interacting with the real
                database queries, which are read-only. Each query in the list should contain 'time' and 'sql' keys.

        Returns:
            Optional[str]: The formatted string of SQL queries or None if no queries were executed.

        This method fetches SQL queries executed after the request started by slicing the `connection.queries`
        list from `initial_queries` onward. For testing purposes, the `test_queries` argument can be used to
        pass simulated query data, allowing the logging logic to be tested without relying on actual database interactions.

        Example of test_queries format:
            test_queries = [{'time': '0.02', 'sql': 'SELECT * FROM table_name'}]

        """
        # Use test queries if provided, otherwise fetch real queries from the database connection.
        new_queries = test_queries or connection.queries[initial_queries:]

        if not new_queries:
            return None

        # Build the query messages in a single pass.
        query_messages = [
            f"\t\tQuery{idx}={{'Time': {query['time']}(s), 'Query': [{query['sql']}]}}\n\t"
            for idx, query in enumerate(new_queries, start=1)
        ]

        # Return the final formatted message.
        return (
            f"{len(new_queries)} SQL QUERIES EXECUTED\n"
            + "\n".join(query_messages)
            + "\n"
        )
