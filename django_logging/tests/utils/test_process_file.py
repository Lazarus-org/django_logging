import os
import sys
from unittest.mock import Mock, patch

import pytest

from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON
from django_logging.utils.command.process_file import setup_directories

pytestmark = [
    pytest.mark.utils,
    pytest.mark.utils_process_file,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


class TestProcessFile:
    """
    Test suite for the process_file module focusing on FileNotFoundError.
    """

    @patch("os.path.exists", return_value=False)
    def test_log_directory_not_found(self, mock_exists: Mock) -> None:
        """
        Test if setup_directories raises FileNotFoundError when the log directory does not exist.

        Args:
        ----
            mock_exists (Callable): Mock for os.path.exists.
        """
        log_dir = "/non/existent/log_dir"
        sub_dir = "sub_dir"

        with pytest.raises(FileNotFoundError, match=f"does not exist."):
            setup_directories(log_dir, sub_dir)

        mock_exists.assert_called_once_with(log_dir)

    @patch("os.path.exists", side_effect=[True, False])
    def test_sub_directory_not_found(self, mock_exists: Mock) -> None:
        """
        Test if setup_directories raises FileNotFoundError when the subdirectory does not exist.

        Args:
        ----
            mock_exists (Callable): Mock for os.path.exists.
        """
        log_dir = "/existent/log_dir"
        sub_dir = "sub_dir"
        sub_directory = os.path.join(log_dir, sub_dir)

        with pytest.raises(FileNotFoundError, match=f"does not exist."):
            setup_directories(log_dir, sub_dir)

        mock_exists.assert_any_call(log_dir)
        mock_exists.assert_any_call(sub_directory)
