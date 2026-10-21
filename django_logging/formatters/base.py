"""Shared, resource-bounded serialization for structured log formatters."""

import datetime
import decimal
import logging
import math
import re
import sys
import traceback
from collections.abc import Mapping
from logging import Formatter, LogRecord
from typing import Any, Dict, List, Optional, Union

from django_logging.constants.structured_validation import resolve_structured_logging

# Only explicitly named structured values can be reliably redacted. Free-form
# messages and exception text may contain secrets and require caller discipline.
_DEFAULT_SECRET_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "session",
    "credential",
    "private_key",
    "api_key",
    "access_key",
    "refresh_token",
    "csrf",
    "otp",
    "phone",
    "mobile",
    "email",
    "national_code",
    "verification_code",
    "signature",
)
_REDACTED = "[REDACTED]"
_OMITTED = "[OMITTED]"
_TEXT_EXPANSION_FACTOR = 6  # covers JSON/XML escaping conservatively
_HARD_NODE_LIMIT = 10_000

# LogRecord keys are not necessarily all specified by a format string; extra={}
# attributes live on the record itself. Do not duplicate framework internals.
_STANDARD_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
    "context",
    "exc_text",
    "taskName",
}


class BaseStructuredFormatter(Formatter):
    """Formatter base compatible with existing ``fmt``/``datefmt`` arguments.

    ``structured_logging`` is optional and can be passed by dictConfig.
    The serializer applies node and conservative output-byte budgets
    while walking values, before building large nested containers or
    invoking a serializer.

    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        *,
        structured_logging: Optional[dict] = None,
    ) -> None:
        super().__init__(fmt, datefmt)
        self.specifiers = self._extract_specifiers(fmt)
        self.options = resolve_structured_logging(structured_logging)
        self._redact_names = frozenset(
            self._normalize_name(name) for name in self.options["REDACT_FIELDS"]
        )
        self._sensitive_cache: Dict[str, bool] = {}

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")

    def _is_sensitive(self, name: str) -> bool:
        # Normalization and caching are cheap for common field names. A very
        # long key is not useful in a log event and may hide a sensitive suffix;
        # redact its value without scanning or normalizing the entire key.
        if len(name) > 256:
            return True
        cached = self._sensitive_cache.get(name)
        if cached is not None:
            return cached
        normalized = self._normalize_name(name)
        result = normalized in self._redact_names or any(
            part in normalized for part in _DEFAULT_SECRET_PARTS
        )
        # Keep this cache bounded because custom applications can supply keys.
        if len(self._sensitive_cache) < 512:
            self._sensitive_cache[name] = result
        return result

    def _extract_specifiers(self, fmt: Optional[str]) -> List[str]:
        return re.findall(r"%\((.*?)\)", fmt) if fmt is not None else []

    def _get_field_value(self, record: LogRecord, specifier: str) -> Optional[Any]:
        if specifier == "message":
            return record.getMessage()
        if specifier == "asctime":
            return self.formatTime(record, self.datefmt)
        return getattr(record, specifier, None)

    def _new_budget(self, *, message: bool = False) -> list[int]:
        """Return ``[remaining_nodes, remaining_escaped_bytes]``.

        Node count is capped independently of user settings, and also
        scales down for small event limits. Text is charged at six
        output bytes per UTF-8 byte to leave room for JSON/XML escaping
        and structural overhead.

        """
        max_event_bytes = self.options["MAX_EVENT_BYTES"]
        configured_nodes = self.options["MAX_ITEMS"] * self.options["MAX_DEPTH"]
        event_nodes = max(8, max_event_bytes // 32)
        nodes = min(configured_nodes, event_nodes, _HARD_NODE_LIMIT)
        byte_budget = max_event_bytes if message else max_event_bytes // 2
        return [max(1, nodes), byte_budget]

    @staticmethod
    def _consume_cost(budget: list[int], cost: int) -> bool:
        if cost > budget[1]:
            # Once a scalar cannot fit, stop traversing sibling values too.
            budget[1] = 0
            return False
        budget[1] -= cost
        return True

    @staticmethod
    def _marker(value: str, budget: list[int]) -> str:
        cost = len(value) * _TEXT_EXPANSION_FACTOR
        if cost > budget[1]:
            budget[1] = 0
            return _OMITTED
        budget[1] -= cost
        return value

    def _sanitize_text(self, value: str, budget: list[int]) -> str:
        """Bound text before returning it to a container or serializer."""
        if not value:
            return ""
        max_chars = min(self.options["MAX_STRING_LENGTH"], len(value))
        raw_limit = budget[1] // _TEXT_EXPANSION_FACTOR
        if raw_limit <= 0:
            return _OMITTED
        max_chars = min(max_chars, raw_limit)

        # Slice before encoding: a multi-megabyte input string only produces a
        # small bounded temporary. Decode after byte truncation so a UTF-8 code
        # point is never cut in half and lone surrogates cannot break encoding.
        candidate = value[:max_chars]
        if candidate.isascii():
            # This is the overwhelmingly common case for keys and ordinary log
            # messages; avoid an encode/decode round trip on the hot path.
            budget[1] -= len(candidate) * _TEXT_EXPANSION_FACTOR
            return candidate
        encoded = candidate.encode("utf-8", errors="replace")
        if len(encoded) > raw_limit:
            encoded = encoded[:raw_limit]
        text = encoded.decode("utf-8", errors="ignore")
        if not text and candidate:
            budget[1] = 0
            return _OMITTED
        cost = len(text.encode("utf-8")) * _TEXT_EXPANSION_FACTOR
        budget[1] -= cost
        return text

    def _sanitize(
        self,
        value: Any,
        *,
        key: str = "",
        depth: int = 0,
        seen: Optional[set[int]] = None,
        budget: Optional[list[int]] = None,
    ) -> Any:
        """Return a safe JSON/XML-compatible value within a shared budget.

        ``budget`` retains support for the old private one-element list
        form; a byte budget is appended when a caller supplies that
        form.

        """
        # Keep the bounded type dispatcher together on the serialization hot path.
        # pylint: disable=too-many-return-statements,too-many-branches
        if budget is None:
            budget = self._new_budget()
        elif len(budget) < 2:
            budget.append(self.options["MAX_EVENT_BYTES"] // 2)

        if budget[0] <= 0:
            return _OMITTED
        budget[0] -= 1
        if budget[1] < _TEXT_EXPANSION_FACTOR:
            return _OMITTED

        if key and self._is_sensitive(key):
            return self._marker(_REDACTED, budget)

        if value is None:
            return None if self._consume_cost(budget, 24) else _OMITTED
        if isinstance(value, bool):
            token = "true" if value else "false"
            return (
                value
                if self._consume_cost(budget, len(token) * _TEXT_EXPANSION_FACTOR)
                else _OMITTED
            )
        if isinstance(value, int):
            # bit_length estimates decimal output length without converting a
            # potentially enormous integer to a string.
            digits = 1 if value == 0 else (value.bit_length() * 30103) // 100000 + 2
            conversion_limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
            if conversion_limit and digits > conversion_limit:
                return self._marker(_OMITTED, budget)
            return (
                value
                if self._consume_cost(budget, digits * _TEXT_EXPANSION_FACTOR)
                else _OMITTED
            )
        if isinstance(value, float):
            if not math.isfinite(value):
                return None if self._consume_cost(budget, 24) else _OMITTED
            return (
                value
                if self._consume_cost(budget, len(repr(value)) * _TEXT_EXPANSION_FACTOR)
                else _OMITTED
            )
        if isinstance(value, str):
            return self._sanitize_text(value, budget)
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            return self._sanitize_text(value.isoformat(), budget)
        if isinstance(value, decimal.Decimal):
            # Avoid converting a Decimal with an excessive number of digits to
            # a giant string only to truncate it afterwards.
            digit_count = len(value.as_tuple().digits)
            if (
                digit_count > self.options["MAX_STRING_LENGTH"]
                or digit_count * _TEXT_EXPANSION_FACTOR > budget[1]
            ):
                return _OMITTED
            return self._sanitize_text(str(value), budget)
        if isinstance(value, (bytes, bytearray, memoryview)):
            return self._marker("[binary omitted]", budget)
        if depth >= self.options["MAX_DEPTH"]:
            return self._marker(_OMITTED, budget)

        if isinstance(value, (Mapping, list, tuple, set, frozenset)):
            if seen is None:
                seen = set()
            if id(value) in seen:
                return self._marker("[circular]", budget)
            seen.add(id(value))
            try:
                if isinstance(value, Mapping):
                    result: Dict[str, Any] = {}
                    for index, (raw_key, item) in enumerate(value.items()):
                        if (
                            index >= self.options["MAX_ITEMS"]
                            or budget[0] <= 0
                            or budget[1] < _TEXT_EXPANSION_FACTOR
                        ):
                            result["_truncated"] = True
                            break
                        original_name = (
                            raw_key if isinstance(raw_key, str) else "[non-string key]"
                        )
                        name = self._sanitize_text(original_name, budget)
                        if name == _OMITTED:
                            result["_truncated"] = True
                            break
                        # Use the original key for redaction before truncation,
                        # so a long key cannot hide a sensitive suffix.
                        result[name] = self._sanitize(
                            item,
                            key=original_name,
                            depth=depth + 1,
                            seen=seen,
                            budget=budget,
                        )
                    return result

                result_list: List[Any] = []
                for index, item in enumerate(value):
                    if (
                        index >= self.options["MAX_ITEMS"]
                        or budget[0] <= 0
                        or budget[1] < _TEXT_EXPANSION_FACTOR
                    ):
                        result_list.append(_OMITTED)
                        break
                    result_list.append(
                        self._sanitize(item, depth=depth + 1, seen=seen, budget=budget)
                    )
                return result_list
            finally:
                seen.remove(id(value))

        # Do not call an arbitrary object's __str__/__repr__: it may reveal data
        # or execute unpredictable code in the logging hot path.
        return self._marker("[unsupported object]", budget)

    def _handle_complex_value(
        self, value: Any
    ) -> Union[str, Dict[str, Any], List[Any], None]:
        """Kept for compatibility with existing formatter subclasses."""
        return self._sanitize(value)

    def _event(self, record: LogRecord) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        budget = self._new_budget()
        # Give the message its own small budget so an oversized extra payload
        # cannot consume all resources before the primary event description.
        safe_message = self._sanitize(
            record.getMessage(), key="message", budget=self._new_budget(message=True)
        )
        for name in self.specifiers:
            if name == "message":
                result[name] = safe_message
                continue
            value = self._get_field_value(record, name)
            if value is not None:
                result[name] = self._sanitize(value, key=name, budget=budget)
        # Keep message intact; never parse or remove key=value fragments.
        result["message"] = safe_message
        if (
            self.options["INCLUDE_EXTRA"]
            and budget[0] > 0
            and budget[1] >= _TEXT_EXPANSION_FACTOR
        ):
            extra: Dict[str, Any] = {}
            for name, value in vars(record).items():
                if (
                    name in _STANDARD_RECORD_FIELDS
                    or name in self.specifiers
                    or name == "context"
                ):
                    continue
                if (
                    len(extra) >= self.options["MAX_ITEMS"]
                    or budget[0] <= 0
                    or budget[1] < _TEXT_EXPANSION_FACTOR
                ):
                    extra["_truncated"] = True
                    break
                extra[name] = value
            if extra:
                result["extra"] = self._sanitize(extra, budget=budget)
        exception = self._exception_value(record, budget=budget)
        if exception is not None:
            result["exception"] = exception
        return result

    def _exception_value(
        self, record: LogRecord, *, budget: Optional[list[int]] = None
    ) -> Optional[str]:
        if not record.exc_info or self.options["EXCEPTION_MODE"] == "omit":
            return None
        if budget is None:
            budget = self._new_budget()
        if self.options["EXCEPTION_MODE"] == "type":
            name = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
            return self._sanitize(name, budget=budget)

        # Limit traceback frame processing and output length. Locals are never
        # captured, as they can be both expensive and sensitive.
        if budget[0] <= 0 or budget[1] < _TEXT_EXPANSION_FACTOR:
            return _OMITTED
        exception = traceback.TracebackException(
            record.exc_info[0],
            record.exc_info[1],
            record.exc_info[2],
            limit=self.options["MAX_EXCEPTION_FRAMES"],
            capture_locals=False,
        )
        char_limit = min(
            self.options["MAX_STRING_LENGTH"],
            max(0, budget[1] // _TEXT_EXPANSION_FACTOR),
        )
        parts: List[str] = []
        remaining = char_limit
        for line in exception.format():
            if remaining <= 0:
                break
            piece = line[:remaining]
            parts.append(piece)
            remaining -= len(piece)
            if len(piece) < len(line):
                break
        return self._sanitize("".join(parts), budget=budget)

    def _add_exception(self, record: LogRecord, data: Dict[str, Any]) -> None:
        exception = self._exception_value(record)
        if exception is not None:
            data["exception"] = exception
