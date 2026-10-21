"""Low-overhead Django HTTP completion logging with opt-in bounded diagnostics.

The normal path emits a single completion event and never evaluates a
lazy session user merely to obtain logging metadata. Request state is
local, not stored on the middleware instance shared between concurrent
requests.

"""

import asyncio
import json
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any, AsyncGenerator, Awaitable, Callable, Generator, Optional, Union
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.core.exceptions import ImproperlyConfigured, TooManyFieldsSent
from django.db import connection
from django.http import HttpRequest, HttpResponseBase, StreamingHttpResponse
from django.utils.functional import SimpleLazyObject, empty

from django_logging.contextvar import manager
from django_logging.middleware.base import BaseMiddleware
from django_logging.settings.manager import SettingsManager
from django_logging.settings.request_logging import normalized_request_logging
from django_logging.utils.redaction import (
    REDACTED,
    diagnostic_json,
    is_sensitive_field,
    redact_values,
    safe_error_response,
    sanitize_user_agent,
)
from django_logging.utils.request import get_ip_address as resolve_client_ip

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RequestLogState:
    """Mutable request-local bookkeeping that never belongs to middleware
    self."""

    request_id: str
    started_at: float
    context: dict[str, str]
    initial_queries: Optional[int] = None
    query: Optional[str] = None
    body: Optional[str] = None


# Compile configuration once; avoid dictionary lookups on every request.
class RequestLogMiddleware(
    BaseMiddleware
):  # pylint: disable=too-many-instance-attributes
    sync_capable = True
    async_capable = True

    def __init__(
        self,
        get_response: Callable[
            [HttpRequest], Union[HttpResponseBase, Awaitable[HttpResponseBase]]
        ],
    ) -> None:
        super().__init__(get_response)
        current = SettingsManager()
        try:
            config = normalized_request_logging(current.request_logging)
        except ValueError as exc:
            raise ImproperlyConfigured(
                f"Invalid DJANGO_LOGGING.REQUEST_LOGGING: {exc}"
            ) from exc

        self.log_sql = current.log_sql_queries_enabled
        self.log_started = config["LOG_REQUEST_STARTED"]
        self.log_finished = config["LOG_REQUEST_FINISHED"]
        self.log_user_agent = config["LOG_USER_AGENT"]
        self.log_query = config["LOG_QUERY_PARAMS"]
        self.log_body = config["LOG_REQUEST_BODY"]
        self.log_errors = config["LOG_ERROR_RESPONSE"]
        self.log_streaming_events = config["LOG_STREAMING_EVENTS"]
        self.excluded_paths = frozenset(config["EXCLUDED_PATHS"])
        self.excluded_path_prefixes = tuple(
            prefix.rstrip("/") for prefix in config["EXCLUDED_PATH_PREFIXES"]
        )
        self.excluded_fields = self._compile_names(config["EXCLUDED_FIELDS"])
        self.excluded_fields_by_path = {
            path: self.excluded_fields | self._compile_names(names)
            for path, names in config["EXCLUDED_FIELDS_BY_PATH"].items()
        }
        self.max_query_bytes = config["MAX_QUERY_BYTES"]
        self.max_body_bytes = config["MAX_BODY_BYTES"]
        self.max_error_bytes = config["MAX_ERROR_BYTES"]
        self.max_sql_bytes = config["MAX_SQL_BYTES"]
        self.max_depth = config["MAX_DIAGNOSTIC_DEPTH"]
        self.max_request_id_length = config["MAX_REQUEST_ID_LENGTH"]
        self.trusted_proxy_cidrs = tuple(config["TRUSTED_PROXY_CIDRS"])

    @staticmethod
    def _compile_names(names: list[str] | tuple[str, ...]) -> frozenset[str]:
        return frozenset(
            name.casefold().replace("-", "_").replace(".", "_") for name in names
        )

    def _values_excluded(self, path: str) -> bool:
        if path in self.excluded_paths:
            return True
        return any(
            prefix == ""
            or path == prefix
            or path.startswith(prefix + "/")
            or path.startswith(prefix + ".")
            for prefix in self.excluded_path_prefixes
        )

    def _exclusions(self, path: str) -> frozenset[str]:
        return self.excluded_fields_by_path.get(path, self.excluded_fields)

    @staticmethod
    def _safe_path(path: str) -> str:
        bounded = path[:256]
        # Most request paths are already printable. Avoid a Python-level
        # character-by-character allocation on this common hot path.
        if bounded.isprintable():
            return bounded
        return "".join(char if char.isprintable() else "?" for char in bounded)

    def __sync_call__(self, request: HttpRequest) -> HttpResponseBase:
        state = self._prepare_request(request)
        with manager.scoped_context(**state.context):
            self._log_start(request, state)
            if self._sql_enabled(request):
                state.initial_queries = self._query_count()
            response = self.get_response(request)
            self._wrap_stream(response, state)
            self._finalize_request(request, response, state)
            return response

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        state = self._prepare_request(request)
        with manager.scoped_context(**state.context):
            self._log_start(request, state)
            if self._sql_enabled(request):
                # Django DB connections are thread-local; run both reads on its
                # thread-sensitive executor, and never do this on the default path.
                state.initial_queries = await sync_to_async(
                    self._query_count, thread_sensitive=True
                )()
            try:
                response = await self.get_response(request)
            except asyncio.CancelledError:
                logger.warning("Request was cancelled: request_id=%s", state.request_id)
                raise
            self._wrap_stream(response, state)
            if self._sql_enabled(request):
                await sync_to_async(self._finalize_request, thread_sensitive=True)(
                    request, response, state
                )
            else:
                self._finalize_request(request, response, state)
            return response

    def _sql_enabled(self, request: HttpRequest) -> bool:
        return (
            self.log_sql
            and self.log_finished
            and self.max_sql_bytes > 0
            and logger.isEnabledFor(logging.INFO)
            and not self._values_excluded(request.path)
        )

    def _prepare_request(self, request: HttpRequest) -> RequestLogState:
        requested_id = self.get_request_id(request)
        valid = (
            isinstance(requested_id, str)
            and requested_id.isascii()
            and 0 < len(requested_id) <= self.max_request_id_length
            and all(char.isalnum() or char in "-_." for char in requested_id)
        )
        request_id = requested_id if valid else str(uuid4())
        request.request_id = request_id
        context = {
            "request_id": request_id,
            "ip_address": self.get_ip_address(request),
        }
        if self.log_user_agent:
            context["user_agent"] = sanitize_user_agent(self.get_user_agent(request))
        state = RequestLogState(
            request_id=request_id, started_at=perf_counter(), context=context
        )
        if (
            self.log_finished
            and logger.isEnabledFor(logging.INFO)
            and not self._values_excluded(request.path)
        ):
            if self.log_query:
                state.query = self._query_values(request)
            if self.log_body:
                state.body = self._request_body_values(request)
        return state

    def _log_start(self, request: HttpRequest, state: RequestLogState) -> None:
        if self.log_started and logger.isEnabledFor(logging.INFO):
            logger.info(
                "REQUEST STARTED: method=%s path=%s request_id=%s",
                request.method,
                self._safe_path(request.path),
                state.request_id,
            )

    def _query_values(self, request: HttpRequest) -> Optional[str]:
        raw = request.META.get("QUERY_STRING", "")
        if not raw:
            return None
        if (
            not isinstance(raw, str)
            or len(raw) > self.max_query_bytes
            or len(raw.encode("utf-8", errors="replace")) > self.max_query_bytes
        ):
            return "<oversized query string>"
        excluded = self._exclusions(request.path)
        try:
            values = {
                key: (
                    REDACTED
                    if is_sensitive_field(key, excluded)
                    else items[0] if len(items) == 1 else items
                )
                for key, items in request.GET.lists()
            }
        except (ValueError, UnicodeError, TooManyFieldsSent):
            return "<unparseable query string>"
        return diagnostic_json(
            values, max_bytes=self.max_query_bytes, oversized="<oversized query string>"
        )

    def _request_body_values(self, request: HttpRequest) -> Optional[str]:
        # Early exits avoid reading unsupported, consumed, or oversized bodies.
        # pylint: disable=too-many-return-statements
        if request.method not in ("POST", "PUT", "PATCH"):
            return None
        if (
            "application/json" not in (request.content_type or "").lower()
            and "+json" not in (request.content_type or "").lower()
        ):
            return None
        try:
            declared = int(request.META.get("CONTENT_LENGTH", ""))
            if not 0 < declared <= self.max_body_bytes:
                return None
            raw = request.body
            if len(raw) > self.max_body_bytes:
                return None
            payload = json.loads(raw)
        except Exception:  # pylint: disable=broad-exception-caught
            # Request body may have been consumed by earlier middleware; never
            # alter request behavior merely because diagnostics are enabled.
            return None
        if not isinstance(payload, (dict, list)):
            return None
        return diagnostic_json(
            redact_values(
                payload, self._exclusions(request.path), max_depth=self.max_depth
            ),
            max_bytes=self.max_body_bytes,
            oversized="<oversized request body>",
        )

    def _safe_error_body(self, response: HttpResponseBase, path: str) -> str:
        if isinstance(response, StreamingHttpResponse):
            return "<streaming error response>"
        chunks = getattr(response, "_container", None)
        if not isinstance(chunks, (tuple, list)):
            return "<error details unavailable>"
        total = 0
        for chunk in chunks:
            if not isinstance(chunk, bytes):
                return "<error details unavailable>"
            total += len(chunk)
            if total > self.max_error_bytes:
                return "<oversized error response>"
        try:
            return safe_error_response(
                response.content,
                response.get("Content-Type", ""),
                max_bytes=self.max_error_bytes,
                excluded_fields=self._exclusions(path),
                max_depth=self.max_depth,
            )
        # Diagnostic adapters must not turn a response into an exception.
        except Exception:  # pylint: disable=broad-exception-caught
            return "<error details unavailable>"

    def _finalize_request(
        self, request: HttpRequest, response: HttpResponseBase, state: RequestLogState
    ) -> None:
        if not self.log_finished or not logger.isEnabledFor(logging.INFO):
            return
        sql_log = ""
        if state.initial_queries is not None:
            sql_log = self._log_sql_queries(state.initial_queries) or ""
        error_summary = None
        if (
            self.log_errors
            and response.status_code >= 400
            and not self._values_excluded(request.path)
        ):
            error_summary = self._safe_error_body(response, request.path)
        logger.info(
            "REQUEST FINISHED: method=%s path=%s user=%s status_code=%d "
            "content_type=%s response_time_ms=%.3f response=%s query_params=%s "
            "request_payload=%s sql=%s",
            request.method,
            self._safe_path(request.path),
            self.get_user(request),
            response.status_code,
            self._safe_path(response.get("Content-Type", "Unknown")),
            (perf_counter() - state.started_at) * 1000,
            error_summary,
            state.query,
            state.body,
            sql_log,
        )

    def _wrap_stream(self, response: HttpResponseBase, state: RequestLogState) -> None:
        if not isinstance(response, StreamingHttpResponse):
            return
        stream = response.streaming_content

        # Django retains source closers separately from streaming_content.
        # Keep their ordering and exception behavior, but run cleanup in the
        # same request context as iteration, including an unstarted stream.
        def contextual_close(close: Callable[[], None]) -> Callable[[], None]:
            def close_with_context() -> None:
                with manager.scoped_context(**state.context):
                    close()

            return close_with_context

        response._resource_closers[:] = [
            contextual_close(close) for close in response._resource_closers
        ]
        if response.is_async:
            response.streaming_content = self._async_streaming_wrapper(
                stream, state.request_id, state.context
            )
        else:
            response.streaming_content = self._sync_streaming_wrapper(
                stream, state.request_id, state.context
            )

    def _sync_streaming_wrapper(
        self,
        streaming_content: Generator[bytes, None, None],
        request_id: str,
        context: Optional[dict[str, str]] = None,
    ) -> Generator[bytes, None, None]:
        # Never hold context tokens across yield: response chunks may be
        # consumed or the iterator closed by a different execution context.
        stream_context = context or {"request_id": request_id}
        iterator = None
        if self.log_streaming_events:
            with manager.scoped_context(**stream_context):
                logger.info("Streaming started: request_id=%s", request_id)
        try:
            iterator = iter(streaming_content)
            while True:
                try:
                    with manager.scoped_context(**stream_context):
                        chunk = next(iterator)
                except StopIteration:
                    break
                yield chunk
        except GeneratorExit:
            if self.log_streaming_events:
                with manager.scoped_context(**stream_context):
                    logger.info("Streaming closed: request_id=%s", request_id)
            raise
        except Exception:
            with manager.scoped_context(**stream_context):
                logger.exception("Streaming failed: request_id=%s", request_id)
            raise
        else:
            if self.log_streaming_events:
                with manager.scoped_context(**stream_context):
                    logger.info("Streaming finished: request_id=%s", request_id)
        finally:
            close = getattr(iterator, "close", None)
            if close is not None:
                with manager.scoped_context(**stream_context):
                    close()

    async def _async_streaming_wrapper(
        self,
        streaming_content: AsyncGenerator[bytes, None],
        request_id: str,
        context: Optional[dict[str, str]] = None,
    ) -> AsyncGenerator[bytes, None]:
        stream_context = context or {"request_id": request_id}
        iterator = None
        if self.log_streaming_events:
            with manager.scoped_context(**stream_context):
                logger.info("Streaming started: request_id=%s", request_id)
        try:
            iterator = aiter(streaming_content)
            while True:
                try:
                    with manager.scoped_context(**stream_context):
                        chunk = await anext(iterator)
                except StopAsyncIteration:
                    break
                yield chunk
        except asyncio.CancelledError:
            if self.log_streaming_events:
                with manager.scoped_context(**stream_context):
                    logger.warning("Streaming was cancelled: request_id=%s", request_id)
            raise
        except GeneratorExit:
            if self.log_streaming_events:
                with manager.scoped_context(**stream_context):
                    logger.info("Streaming closed: request_id=%s", request_id)
            raise
        except Exception:
            with manager.scoped_context(**stream_context):
                logger.exception("Streaming failed: request_id=%s", request_id)
            raise
        else:
            if self.log_streaming_events:
                with manager.scoped_context(**stream_context):
                    logger.info("Streaming finished: request_id=%s", request_id)
        finally:
            aclose = getattr(iterator, "aclose", None)
            if aclose is not None:
                with manager.scoped_context(**stream_context):
                    await aclose()

    @staticmethod
    def get_user(request: HttpRequest) -> str:
        """Access only already-resolved authentication, without triggering DB
        I/O."""
        values = request.__dict__
        user: Any = values.get("user")
        if isinstance(user, SimpleLazyObject):
            user = user.__dict__.get("_wrapped", empty)
            if user is empty:
                user = None
        if user is None:
            user = values.get("_cached_user") or values.get("_acached_user")
        if user is not None and getattr(user, "is_authenticated", False):
            return f"[user_id={str(user.pk)[:64]}]"
        return "Anonymous"

    def get_ip_address(self, request: HttpRequest) -> str:
        return resolve_client_ip(request, self.trusted_proxy_cidrs) or "Unknown IP"

    @staticmethod
    def get_user_agent(request: HttpRequest) -> str:
        return request.META.get("HTTP_USER_AGENT", "Unknown User Agent")

    @staticmethod
    def get_request_id(request: HttpRequest) -> Optional[str]:
        return request.META.get("HTTP_X_REQUEST_ID")

    @staticmethod
    def _query_count() -> int:
        return len(connection.queries)

    def _log_sql_queries(
        self, initial_queries: int, test_queries: Optional[list[dict]] = None
    ) -> Optional[str]:
        queries = (
            test_queries
            if test_queries is not None
            else connection.queries[initial_queries:]
        )
        if not queries:
            return None
        # Preserve the detailed SQL format but avoid accumulating arbitrarily
        # large strings. SQL is sensitive: only capture with explicit opt-in.
        header = f"{len(queries)} SQL QUERIES EXECUTED\n"
        lines = [header]
        used = len(header.encode("utf-8"))
        for index, query in enumerate(queries, start=1):
            line = f"\t\tQuery{index}={{'Time': {query['time']}(s), 'Query': [{query['sql']}]}}\n\t"
            used += len(line.encode("utf-8"))
            if used > self.max_sql_bytes:
                return "<oversized SQL log>"
            lines.append(line)
        return "\n".join(lines) + "\n"
