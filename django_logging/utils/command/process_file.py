import os
from typing import Callable, Generator, Tuple


def setup_directories(log_dir: str, sub_dir: str) -> Tuple[str, str]:
    """Set up the directories for processing files.

    Args:
        log_dir (str): The path to the main log directory.
        sub_dir (str): The name of the subdirectory to check for.

    Returns:
        Tuple[str, str]: A tuple containing the paths to the subdirectory and the pretty directory.

    Raises:
        FileNotFoundError: If the log directory or subdirectory does not exist.

    """
    if not os.path.exists(log_dir):
        raise FileNotFoundError(f"Directory {log_dir} does not exist.")

    sub_directory = os.path.join(log_dir, sub_dir)
    if not os.path.exists(sub_directory):
        raise FileNotFoundError(f"Directory {sub_directory} does not exist.")

    pretty_dir = os.path.join(sub_directory, "pretty")
    os.makedirs(pretty_dir, exist_ok=True)

    return sub_directory, pretty_dir


def process_files(
    directory: str, file_extension: str, handler_function: Callable
) -> Generator[Tuple[str, str], None, None]:
    """Process files in a directory and apply a handler function to each.

    Args:
        directory (str): The path to the directory containing files.
        file_extension (str): The file extension to filter files by.
        handler_function (Callable): The function to apply to each processed file.

    Yields:
        Generator[Tuple[str, str], None, None]: Yields tuples of file paths and filenames for each processed file.

    """
    for filename in os.listdir(directory):
        if filename.endswith(file_extension):
            file_path = os.path.join(directory, filename)
            yield file_path, filename
