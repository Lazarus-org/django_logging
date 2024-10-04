import pytest

from django_logging.formatters import (
    ColoredFormatter,
    FLATFormatter,
    JSONFormatter,
    XMLFormatter,
)


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


@pytest.fixture
def json_formatter() -> JSONFormatter:
    """
    Fixture to provide an instance of `JSONFormatter`.

    Returns:
    -------
    JSONFormatter: An instance of the `JSONFormatter` with a predefined format.
    """
    return JSONFormatter(fmt="%(levelname)s: %(message)s")


@pytest.fixture
def xml_formatter() -> XMLFormatter:
    """
    Fixture to provide an instance of `XMLFormatter`.

    Returns:
    -------
    XMLFormatter: An instance of the `XMLFormatter` with predefined format.
    """
    return XMLFormatter(fmt="%(levelname)s: %(message)s")


@pytest.fixture
def flat_formatter() -> FLATFormatter:
    """
    Fixture to provide an instance of `FLATFormatter`.

    Returns:
    -------
    FLATFormatter: An instance of the `FLATLineFormatter` with predefined format.
    """
    return FLATFormatter(fmt="%(levelname)s: %(message)s")
