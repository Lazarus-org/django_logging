import sys

import pytest

from django_logging.contextvar.contextvar_manager import ContextVarManager
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.contextvar,
    pytest.mark.contextvar_manager,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestContextVarManager:
    """Tests for the ContextVarManager class."""

    def setup_method(self) -> None:
        """Set up a new ContextVarManager instance before each test."""
        self.manager = ContextVarManager()

    def test_bind_and_get_contextvars(self) -> None:
        """
        Test that variables can be bound and retrieved.
        """
        self.manager.bind(user_id=42, request_id="abc123")

        context_vars = self.manager.get_contextvars()
        assert context_vars["user_id"] == 42
        assert context_vars["request_id"] == "abc123"
        self.manager.clear()

    def test_batch_bind_and_reset(self) -> None:
        """
        Test batch binding context variables and resetting them using tokens.
        """
        tokens = self.manager.batch_bind(user_id=42, request_id="abc123")

        context_vars = self.manager.get_contextvars()
        assert context_vars["user_id"] == 42
        assert context_vars["request_id"] == "abc123"

        self.manager.reset(tokens)
        context_vars = self.manager.get_contextvars()
        assert "user_id" not in context_vars
        assert "request_id" not in context_vars

    def test_unbind(self) -> None:
        """
        Test unbinding a context variable.
        """
        self.manager.bind(user_id=42)
        self.manager.unbind("user_id")

        context_vars = self.manager.get_contextvars()
        assert "user_id" not in context_vars

    def test_clear(self) -> None:
        """
        Test clearing all context variables.
        """
        self.manager.bind(user_id=42, request_id="abc123")
        self.manager.clear()

        context_vars = self.manager.get_contextvars()
        assert "user_id" not in context_vars
        assert "request_id" not in context_vars

    def test_merge_contexts(self) -> None:
        """
        Test merging context variables with priority given to bound context.
        """
        local_context = {"user_id": 42, "request_id": "abc123"}
        bound_context = {"user_id": 99, "role": "admin"}

        merged_context = self.manager.merge_contexts(bound_context, local_context)

        assert merged_context["user_id"] == 99  # bound context should override
        assert merged_context["request_id"] == "abc123"
        assert merged_context["role"] == "admin"
        self.manager.clear()

    def test_get_merged_context(self) -> None:
        """
        Test getting the merged context from both logger-bound and local context variables.
        """
        self.manager.bind(user_id=42, request_id="abc123")
        bound_logger_context = {"user_id": 99, "role": "admin"}

        merged_context = self.manager.get_merged_context(bound_logger_context)

        assert merged_context["user_id"] == 99  # bound context should override
        assert merged_context["request_id"] == "abc123"
        assert merged_context["role"] == "admin"
        self.manager.clear()

    def test_scoped_context(self) -> None:
        """
        Test using the context manager to temporarily bind and reset context variables.
        """
        with self.manager.scoped_context(user_id=42):
            context_vars = self.manager.get_contextvars()
            assert context_vars["user_id"] == 42

        context_vars = self.manager.get_contextvars()
        assert "user_id" not in context_vars


def test_lookup_ignores_unrelated_context_variables(monkeypatch) -> None:
    """Retrieval must inspect only keys registered by this manager."""
    import contextvars

    manager = ContextVarManager()
    manager.bind(request_id="req-1", tenant_id="tenant-1")
    unrelated = contextvars.ContextVar("tracing_context", default=None)
    unrelated.set({"trace_id": "trace-1"})

    def forbidden_copy_context():
        raise AssertionError("get_contextvars must not copy the whole context")

    monkeypatch.setattr(contextvars, "copy_context", forbidden_copy_context)
    assert manager.get_contextvars() == {
        "request_id": "req-1",
        "tenant_id": "tenant-1",
    }


def test_lookup_skips_registered_but_unbound_variables() -> None:
    manager = ContextVarManager()
    tokens = manager.batch_bind(request_id="req-1", tenant_id="tenant-1")
    manager.reset(tokens)
    assert manager.get_contextvars() == {}
