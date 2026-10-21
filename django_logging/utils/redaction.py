"""Opt-in, bounded diagnostic JSON with conservative secret redaction.

Sensitive-field matching is best-effort, not a substitute for disabling
value logging on credential-handling endpoints.

"""

import json
import re
from collections.abc import Collection
from typing import Any

REDACTED = "[REDACTED]"
OMITTED = "[OMITTED]"
SENSITIVE_FIELD_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "session",
    "otp",
    "national_code",
    "nationalcode",
    "phone",
    "mobile",
    "email",
    "credential",
    "private_key",
    "api_key",
    "access_key",
    "refresh",
    "signature",
    "signed_url",
    "csrf",
    "pin",
    "verification_code",
)
_USER_AGENT_PRODUCT = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9_.-]{0,31}/[0-9][A-Za-z0-9_.-]{0,31})"
)
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def is_sensitive_field(name: str, excluded_fields: Collection[str] = ()) -> bool:
    normalized = name.casefold().replace("-", "_").replace(".", "_")
    return normalized in excluded_fields or any(
        part in normalized for part in SENSITIVE_FIELD_PARTS
    )


def redact_values(
    value: Any,
    excluded_fields: Collection[str] = (),
    *,
    max_depth: int,
    _depth: int = 0,
) -> Any:
    if _depth >= max_depth and isinstance(value, (dict, list)):
        return OMITTED
    if isinstance(value, dict):
        return {
            key: (
                REDACTED
                if is_sensitive_field(key, excluded_fields)
                else redact_values(
                    item, excluded_fields, max_depth=max_depth, _depth=_depth + 1
                )
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            redact_values(item, excluded_fields, max_depth=max_depth, _depth=_depth + 1)
            for item in value
        ]
    return value


def diagnostic_json(value: Any, *, max_bytes: int, oversized: str) -> str:
    """Bound serialized output as well as input (Unicode escaping can
    expand)."""
    try:
        text = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        return text if len(text.encode("utf-8")) <= max_bytes else oversized
    except (ValueError, TypeError, RecursionError, OverflowError):
        return "<unserializable diagnostic>"


def safe_error_response(
    raw_body: bytes,
    content_type: str,
    *,
    max_bytes: int,
    max_depth: int,
    excluded_fields: Collection[str] = (),
) -> str:
    if (
        "application/json" not in content_type.lower()
        and "+json" not in content_type.lower()
    ):
        return "<non-json error response>"
    if len(raw_body) > max_bytes:
        return "<oversized error response>"
    try:
        parsed = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError, TypeError, RecursionError):
        return "<unparseable error response>"
    if not isinstance(parsed, dict):
        return "<unstructured error response>"
    return diagnostic_json(
        redact_values(parsed, excluded_fields, max_depth=max_depth),
        max_bytes=max_bytes,
        oversized="<oversized error response>",
    )


def sanitize_user_agent(value: str, *, max_length: int = 180) -> str:
    products = _USER_AGENT_PRODUCT.findall(_CONTROL.sub(" ", str(value))[:2048])
    return (" ".join(products[:6]) or "Unknown User Agent")[:max_length]
