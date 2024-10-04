from logging import LogRecord

from django_logging.formatters.base import BaseStructuredFormatter


class FLATFormatter(BaseStructuredFormatter):
    """A custom log formatter that formats log records as a single flat line
    string, with key-value pairs like `asctime='2019-04-13' level='INFO'`."""

    def format(self, record: LogRecord) -> str:
        """Formats the log record as a flat line string.

        Args:
        ----
            record (logging.LogRecord): The log record object.

        Returns:
        -------
            str: The formatted flat line string.

        """
        # Build the flat line string based on the specifiers
        flat_line = " ".join(
            f"{specifier}='{self._get_field_value(record, specifier)}'"
            for specifier in self.specifiers
            if self._get_field_value(record, specifier) is not None
        )

        # Add exception information if available
        if record.exc_info:
            flat_line += f" exception='{self.formatException(record.exc_info)}'"

        return flat_line
