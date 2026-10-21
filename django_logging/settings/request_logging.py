"""Validation and normalization of DJANGO_LOGGING.REQUEST_LOGGING."""

from ipaddress import ip_network
from typing import Any

from django_logging.constants.request_logging import (
    REQUEST_LOGGING_BOOLEANS,
    REQUEST_LOGGING_BYTE_LIMITS,
    REQUEST_LOGGING_DEFAULTS,
    REQUEST_LOGGING_LISTS,
)


def request_logging_errors(value: Any) -> list[str]:
    """Return all configuration errors; never silently coerce invalid security
    policies."""
    if not isinstance(value, dict):
        return ["REQUEST_LOGGING must be a dictionary"]
    errors: list[str] = []
    for key, entry in value.items():
        if key not in REQUEST_LOGGING_DEFAULTS:
            errors.append(f"unknown REQUEST_LOGGING option {key!r}")
            continue
        if key in REQUEST_LOGGING_BOOLEANS:
            if type(entry) is not bool:
                errors.append(f"REQUEST_LOGGING.{key} must be a boolean")
        elif key in REQUEST_LOGGING_BYTE_LIMITS:
            if type(entry) is not int or not 0 <= entry <= 1_048_576:
                errors.append(
                    f"REQUEST_LOGGING.{key} must be an integer between 0 and 1048576"
                )
        elif key == "MAX_DIAGNOSTIC_DEPTH":
            if type(entry) is not int or not 1 <= entry <= 32:
                errors.append(
                    "REQUEST_LOGGING.MAX_DIAGNOSTIC_DEPTH must be an integer between 1 and 32"
                )
        elif key == "MAX_REQUEST_ID_LENGTH":
            if type(entry) is not int or not 1 <= entry <= 128:
                errors.append(
                    "REQUEST_LOGGING.MAX_REQUEST_ID_LENGTH must be an integer between 1 and 128"
                )
        elif key in REQUEST_LOGGING_LISTS:
            if not isinstance(entry, (tuple, list)) or any(
                not isinstance(item, str) or not item for item in entry
            ):
                errors.append(
                    f"REQUEST_LOGGING.{key} must be a list of nonempty strings"
                )
                continue
            if key in ("EXCLUDED_PATHS", "EXCLUDED_PATH_PREFIXES"):
                if any(not path.startswith("/") for path in entry):
                    errors.append(f"REQUEST_LOGGING.{key} entries must start with /")
            elif key == "TRUSTED_PROXY_CIDRS":
                for cidr in entry:
                    try:
                        ip_network(cidr, strict=True)
                    except ValueError:
                        errors.append(
                            f"REQUEST_LOGGING.TRUSTED_PROXY_CIDRS contains invalid CIDR {cidr!r}"
                        )
        elif key == "EXCLUDED_FIELDS_BY_PATH":
            if not isinstance(entry, dict):
                errors.append(
                    "REQUEST_LOGGING.EXCLUDED_FIELDS_BY_PATH must be a dictionary"
                )
                continue
            for path, names in entry.items():
                if (
                    not isinstance(path, str)
                    or not path.startswith("/")
                    or not isinstance(names, (tuple, list))
                    or any(not isinstance(name, str) or not name for name in names)
                ):
                    errors.append(
                        "REQUEST_LOGGING.EXCLUDED_FIELDS_BY_PATH requires absolute paths and lists of nonempty field names"
                    )
    return errors


def normalized_request_logging(value: Any) -> dict[str, Any]:
    """Make an independent copy of merged defaults for a middleware
    instance."""
    errors = request_logging_errors(value)
    if errors:
        raise ValueError("; ".join(errors))
    merged = dict(REQUEST_LOGGING_DEFAULTS)
    merged.update(value)
    return merged
