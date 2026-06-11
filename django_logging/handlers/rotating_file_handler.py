"""Custom rotating file handlers that optionally gzip rotated log files."""

import gzip
import os
import shutil
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


def _gzip_namer(default_name: str) -> str:
    """Return the rotated filename with a .gz suffix appended."""
    return default_name + ".gz"


def _gzip_rotator(source: str, dest: str) -> None:
    """Compress *source* into *dest*.gz and remove the original."""
    gz_dest = dest if dest.endswith(".gz") else dest + ".gz"
    with open(source, "rb") as f_in, gzip.open(gz_dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(source)


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
