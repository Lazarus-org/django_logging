"""Safe default configuration and shared request-logging setting names."""

from typing import Any

REQUEST_LOGGING_DEFAULTS: dict[str, Any] = {
    "LOG_REQUEST_STARTED": False,
    "LOG_REQUEST_FINISHED": True,
    "LOG_USER_AGENT": True,
    "LOG_QUERY_PARAMS": False,
    "LOG_REQUEST_BODY": False,
    "LOG_ERROR_RESPONSE": False,
    # Stream context is still propagated when this is disabled; only the
    # additional started/finished/closed/cancelled log events are suppressed.
    "LOG_STREAMING_EVENTS": False,
    "EXCLUDED_PATHS": [],
    "EXCLUDED_PATH_PREFIXES": [],
    "EXCLUDED_FIELDS": [],
    "EXCLUDED_FIELDS_BY_PATH": {},
    "MAX_QUERY_BYTES": 4096,
    "MAX_BODY_BYTES": 2048,
    "MAX_ERROR_BYTES": 2048,
    "MAX_SQL_BYTES": 4096,
    "MAX_DIAGNOSTIC_DEPTH": 8,
    "TRUSTED_PROXY_CIDRS": [],
    "MAX_REQUEST_ID_LENGTH": 80,
}

REQUEST_LOGGING_BOOLEANS = frozenset(
    {
        "LOG_REQUEST_STARTED",
        "LOG_REQUEST_FINISHED",
        "LOG_USER_AGENT",
        "LOG_QUERY_PARAMS",
        "LOG_REQUEST_BODY",
        "LOG_ERROR_RESPONSE",
        "LOG_STREAMING_EVENTS",
    }
)
REQUEST_LOGGING_BYTE_LIMITS = frozenset(
    {
        "MAX_QUERY_BYTES",
        "MAX_BODY_BYTES",
        "MAX_ERROR_BYTES",
        "MAX_SQL_BYTES",
    }
)
REQUEST_LOGGING_LISTS = frozenset(
    {
        "EXCLUDED_PATHS",
        "EXCLUDED_PATH_PREFIXES",
        "EXCLUDED_FIELDS",
        "TRUSTED_PROXY_CIDRS",
    }
)
