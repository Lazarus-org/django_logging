from typing import Awaitable, Callable, Union

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponseBase


class BaseMiddleware:
    sync_capable: bool = True
    async_capable: bool = True

    def __init__(
        self,
        get_response: Callable[
            [HttpRequest], Union[HttpResponseBase, Awaitable[HttpResponseBase]]
        ],
    ) -> None:
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            markcoroutinefunction(self)

    def __repr__(self) -> str:
        """Provides a string representation of the middleware."""
        ger_response = getattr(
            self.get_response,
            "__qualname__",
            self.get_response.__class__.__name__,
        )
        return f"<{self.__class__.__qualname__} get_response={ger_response}>"

    def __call__(
        self, request: HttpRequest
    ) -> Union[HttpResponseBase, Awaitable[HttpResponseBase]]:
        """Handles the incoming request, determining whether it's synchronous
        or asynchronous.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            Union[HttpResponseBase, Awaitable[HttpResponseBase]]: The HTTP response, either synchronous or asynchronous.

        """
        if self.async_mode:
            return self.__acall__(request)
        return self.__sync_call__(request)

    def __sync_call__(self, request: HttpRequest) -> HttpResponseBase:
        raise NotImplementedError("__sync_call__ must be implemented by subclass")

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        raise NotImplementedError("__acall__ must be implemented by subclass")
