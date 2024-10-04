import contextvars
from contextlib import contextmanager
from typing import Any, Dict, Generator


class ContextVarManager:
    """A manager for handling context variables in a Django logging
    environment.

    This class manages the creation, binding, resetting, and merging of
    context variables, with an additional feature to support scoped binding
    of context variables during specific blocks of code execution.

    Attributes:
        DJANGO_LOGGING_PREFIX (str): Prefix used to namespace the context variables.

    """

    DJANGO_LOGGING_PREFIX = "django_logging_"

    def __init__(self) -> None:
        """Initialize the ContextVarManager.

        Creates an internal dictionary to store `ContextVar` instances.

        """
        self._context_vars: Dict[str, contextvars.ContextVar[Any]] = {}

    # ---- Context Variable Management ----
    def _get_or_create(self, key: str) -> contextvars.ContextVar[Any]:
        """Get an existing ContextVar or create one if it doesn't exist.

        Args:
            key (str): The key used to identify the context variable.

        Returns:
            contextvars.ContextVar: The requested or newly created context variable.

        """
        full_key = f"{self.DJANGO_LOGGING_PREFIX}{key}"
        if full_key not in self._context_vars:
            self._context_vars[full_key] = contextvars.ContextVar(
                full_key, default=None
            )
        return self._context_vars[full_key]

    def bind(self, **kwargs: Any) -> None:
        """Bind multiple context variables.

        Args:
            **kwargs: Key-value pairs to be bound to context variables.

        """
        for key, value in kwargs.items():
            var = self._get_or_create(key)
            var.set(value)

    def batch_bind(self, **kwargs: Any) -> Dict[str, contextvars.Token]:
        """Bind multiple context variables and return tokens for resetting.

        Args:
            **kwargs: Key-value pairs to bind to context variables.

        Returns:
            Dict[str, contextvars.Token]: A dictionary of tokens used to reset the variables later.

        """
        tokens = {}
        for key, value in kwargs.items():
            var = self._get_or_create(key)
            tokens[key] = var.set(value)
        return tokens

    def unbind(self, key: str) -> None:
        """Unbind a specific context variable, effectively removing its value.

        Args:
            key (str): The key of the context variable to unbind.

        """
        full_key = f"{self.DJANGO_LOGGING_PREFIX}{key}"
        if full_key in self._context_vars:
            self._context_vars[full_key].set(Ellipsis)

    def reset(self, tokens: Dict[str, contextvars.Token]) -> None:
        """Reset context variables to their previous state using tokens.

        Args:
            tokens (Dict[str, contextvars.Token]): Tokens representing the previous state of the context variables.

        """
        for key, token in tokens.items():
            var = self._get_or_create(key)
            var.reset(token)

    def clear(self) -> None:
        """Clear all bound context variables."""
        for var in self._context_vars.values():
            var.set(Ellipsis)

    # ---- Context Retrieval and Merging ----
    def get_contextvars(self) -> Dict[str, Any]:
        """Retrieve the current context-local variables.

        Returns:
            Dict[str, Any]: A dictionary of context-local variables.

        """
        rv = {}
        ctx = contextvars.copy_context()
        for k in ctx:
            if k.name.startswith(self.DJANGO_LOGGING_PREFIX) and ctx[k] is not Ellipsis:
                rv[k.name[len(self.DJANGO_LOGGING_PREFIX) :]] = ctx[k]
        return rv

    def merge_contexts(
        self, bound_context: Dict[str, Any], local_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two context dictionaries, giving priority to the bound
        context.

        Args:
            bound_context (Dict[str, Any]): Bound logger context.
            local_context (Dict[str, Any]): Context-local variables.

        Returns:
            Dict[str, Any]: The merged context dictionary.

        """
        merged_context = local_context.copy()
        merged_context.update(bound_context)
        return merged_context

    def get_merged_context(
        self, bound_logger_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get the merged context by combining bound logger context and
        context-local variables.

        Args:
            bound_logger_context (Dict[str, Any]): Bound logger context.

        Returns:
            Dict[str, Any]: The merged context dictionary.

        """
        local_context = self.get_contextvars()
        return self.merge_contexts(bound_logger_context, local_context)

    # ---- Scoped Context Management ----
    @contextmanager
    def scoped_context(self, **kwargs: Any) -> Generator[None, None, None]:
        """Context manager to temporarily bind context variables for a block of
        code.

        Args:
            **kwargs: Key-value pairs to bind as context variables.

        Yields:
            None

        """
        tokens = self.batch_bind(**kwargs)
        try:
            yield
        finally:
            self.reset(tokens)


manager: ContextVarManager = ContextVarManager()
