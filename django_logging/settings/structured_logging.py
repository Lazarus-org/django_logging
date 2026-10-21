"""Compatibility location for the shared structured logging validator."""

from django_logging.constants.structured_validation import (
    resolve_structured_logging,
    structured_logging_errors,
)

__all__ = ["resolve_structured_logging", "structured_logging_errors"]
