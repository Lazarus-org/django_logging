"""Shared, bounded serialization for structured Django log formatters."""

import datetime
import decimal
import logging
import math
import re
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

    ``structured_logging`` is optional and can be passed by dictConfig. This
    allows direct formatter construction without Django settings initialization.
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

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")

    def _is_sensitive(self, name: str) -> bool:
        normalized = self._normalize_name(name)
        return normalized in self._redact_names or any(
            part in normalized for part in _DEFAULT_SECRET_PARTS
        )

    def _extract_specifiers(self, fmt: Optional[str]) -> List[str]:
        return re.findall(r"%\((.*?)\)", fmt) if fmt is not None else []

    def _get_field_value(self, record: LogRecord, specifier: str) -> Optional[Any]:
        if specifier == "message":
            return record.getMessage()
        if specifier == "asctime":
            return self.formatTime(record, self.datefmt)
        return getattr(record, specifier, None)

    def _sanitize(
        self,
        value: Any,
        *,
        key: str = "",
        depth: int = 0,
        seen: Optional[set[int]] = None,
    ) -> Any:
        if key and self._is_sensitive(key):
            return _REDACTED
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, str):
            return value[: self.options["MAX_STRING_LENGTH"]]
        if isinstance(value, (datetime.date, datetime.time, datetime.datetime)):
            return value.isoformat()
        if isinstance(value, decimal.Decimal):
            return str(value)
        if isinstance(value, (bytes, bytearray, memoryview)):
            return "[binary omitted]"
        if depth >= self.options["MAX_DEPTH"]:
            return _OMITTED
        if isinstance(value, (Mapping, list, tuple, set, frozenset)):
            if seen is None:
                seen = set()
            if id(value) in seen:
                return "[circular]"
            seen.add(id(value))
            try:
                if isinstance(value, Mapping):
                    result = {}
                    for index, (raw_key, item) in enumerate(value.items()):
                        if index >= self.options["MAX_ITEMS"]:
                            result["_truncated"] = True
                            break
                        name = (
                            raw_key if isinstance(raw_key, str) else "[non-string key]"
                        )
                        name = name[: self.options["MAX_STRING_LENGTH"]]
                        result[name] = self._sanitize(
                            item, key=name, depth=depth + 1, seen=seen
                        )
                    return result
                result_list = []
                for index, item in enumerate(value):
                    if index >= self.options["MAX_ITEMS"]:
                        result_list.append(_OMITTED)
                        break
                    result_list.append(self._sanitize(item, depth=depth + 1, seen=seen))
                return result_list
            finally:
                seen.remove(id(value))
        # Do not call an arbitrary object's __str__/__repr__: it may reveal data
        # or execute unpredictable code in the logging hot path.
        return "[unsupported object]"

    def _handle_complex_value(
        self, value: Any
    ) -> Union[str, Dict[str, Any], List[Any], None]:
        """Kept for compatibility with existing formatter subclasses."""
        return self._sanitize(value)

    def _event(self, record: LogRecord) -> Dict[str, Any]:
        result = {}
        message = record.getMessage()
        for name in self.specifiers:
            value = (
                message if name == "message" else self._get_field_value(record, name)
            )
            if value is not None:
                result[name] = self._sanitize(value, key=name)
        # Keep message intact; never parse or remove key=value fragments.
        result["message"] = self._sanitize(message, key="message")
        if self.options["INCLUDE_EXTRA"]:
            extra = {
                name: value
                for name, value in vars(record).items()
                if name not in _STANDARD_RECORD_FIELDS
                and name not in self.specifiers
                and name != "context"
            }
            if extra:
                result["extra"] = self._sanitize(extra)
        exception = self._exception_value(record)
        if exception is not None:
            result["exception"] = exception
        return result

    def _exception_value(self, record: LogRecord) -> Optional[str]:
        if not record.exc_info or self.options["EXCEPTION_MODE"] == "omit":
            return None
        if self.options["EXCEPTION_MODE"] == "type":
            return record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        # Existing traceback behavior remains available by default. This text
        # cannot be safely auto-redacted; its length is bounded.
        return self._sanitize(self.formatException(record.exc_info))

    def _add_exception(self, record: LogRecord, data: Dict[str, Any]) -> None:
        exception = self._exception_value(record)
        if exception is not None:
            data["exception"] = exception
