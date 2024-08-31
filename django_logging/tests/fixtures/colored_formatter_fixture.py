import pytest

from django_logging.formatters import ColoredFormatter


@pytest.fixture
def colored_formatter() -> ColoredFormatter:
    """
    Fixture to create a `ColoredFormatter` instance with a specific format.

    Returns:
    -------
    ColoredFormatter
        An instance of `ColoredFormatter` with a predefined format.
    """
    return ColoredFormatter(fmt="%(levelname)s: %(message)s")
