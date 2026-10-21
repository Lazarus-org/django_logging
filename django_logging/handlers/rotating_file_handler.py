"""Custom rotating file handlers that optionally gzip rotated log files."""

import gzip
import os
import shutil
import tempfile
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


def _gzip_namer(default_name: str) -> str:
    """Return the rotated filename with a .gz suffix appended."""
    return default_name + ".gz"


def _gzip_rotator(source: str, dest: str) -> None:
    """Commit a complete gzip file before removing the uncompressed source.

    A failed copy leaves the source intact and removes the incomplete
    archive. This does not make the standard rotating handlers
    multiprocess-safe.

    """
    gz_dest = dest if dest.endswith(".gz") else dest + ".gz"
    fd, tmp = tempfile.mkstemp(
        prefix=".dj-logging-", suffix=".tmp", dir=os.path.dirname(gz_dest)
    )
    try:
        with (
            os.fdopen(fd, "wb") as raw,
            gzip.GzipFile(fileobj=raw, mode="wb") as compressed,
        ):
            with open(source, "rb") as original:
                shutil.copyfileobj(original, compressed)
        os.replace(tmp, gz_dest)
        os.remove(source)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class CompressedRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that gzip-compresses each rotated log file."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotator = _gzip_rotator
        self.namer = _gzip_namer


class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    """TimedRotatingFileHandler that gzip-compresses each rotated log file."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rotator = _gzip_rotator
        self.namer = _gzip_namer
