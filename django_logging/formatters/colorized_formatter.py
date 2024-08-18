import logging
from django_logging.settings.conf import LogConfig
from django_logging.utils.colorizer import colorize_log_format


class ColorizedFormatter(logging.Formatter):
    def format(self, record):
        original_format = self._style._fmt

        # checks that the format does not have any color it's self
        if LogConfig.remove_ansi_escape_sequences(original_format) == original_format:
            colorized_format = colorize_log_format(original_format, record.levelname)
            self._style._fmt = colorized_format

        formatted_output = super().format(record)

        # Reset to the original format string
        self._style._fmt = original_format

        return formatted_output
