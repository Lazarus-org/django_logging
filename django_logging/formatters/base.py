import re
from logging import Formatter, LogRecord
from typing import Any, Dict, List, Optional, Union


class BaseStructuredFormatter(Formatter):
    """Base class for custom formatters that extract specific fields from log
    records based on a format string.

    Attributes:
    ----------
        specifiers (List[str]): List of specifiers extracted from the provided format string.

    """

    def __init__(
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None
    ) -> None:
        """Initializes the formatter by extracting the format specifiers from
        the format string.

        Args:
        ----
            fmt (Optional[str]): The log format string, e.g., "%(levelname)s | %(asctime)s | %(message)s".
            datefmt (Optional[str]): The date format string for formatting 'asctime'.

        """
        super().__init__(fmt, datefmt)
        self.specifiers = self._extract_specifiers(fmt)

    def _extract_specifiers(self, fmt: Optional[str]) -> List[str]:
        """Extracts format specifiers (e.g., %(levelname)s) from the format
        string.

        Args:
        ----
            fmt (Optional[str]): The format string to extract specifiers from.

        Returns:
        -------
            List[str]: A list of extracted specifier names.

        """
        if fmt is None:
            return []
        return re.findall(r"%\((.*?)\)", fmt)

    def _get_field_value(self, record: LogRecord, specifier: str) -> Optional[Any]:
        """Retrieves the value for a given specifier from the log record.

        Args:
        ----
            record (logging.LogRecord): The log record object.
            specifier (str): The field name to retrieve from the log record.

        Returns:
        -------
            Optional[Any]: The value of the field, or None if the field is not found.

        """
        if specifier == "message":
            return record.getMessage()
        elif specifier == "asctime":
            return self.formatTime(record, self.datefmt)
        elif hasattr(record, specifier):
            return getattr(record, specifier)
        return None

    def _handle_complex_value(
        self, value: Any
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """Recursively handles complex values such as dictionaries, lists, and
        datetime objects.

        Args:
        ----
            value (Any): The value to process.

        Returns:
        -------
            Union[str, Dict[str, Any], List[Any]]: The processed value.

        """
        if isinstance(value, dict):
            return {k: self._handle_complex_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._handle_complex_value(v) for v in value]

        return str(value)

    def _add_exception(self, record: LogRecord, data: Dict[str, Any]) -> None:
        """Adds exception information to the data structure, if present in the
        log record.

        Args:
        ----
            record (logging.LogRecord): The log record object.
            data (Dict[str, Any]): The dictionary to which exception information will be added.

        """
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
