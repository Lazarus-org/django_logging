def format_elapsed_time(elapsed_time: float) -> str:
    """Formats the elapsed time into a human-readable string.

    If the time is less than a minute, returns only seconds. Otherwise,
    returns the time in minutes and seconds.

    Args:
        elapsed_time: Time in seconds as a float.

    Returns:
        A string representing the formatted time.

    """
    minutes, seconds = divmod(elapsed_time, 60)

    if minutes > 0:
        return f"{int(minutes)} minute(s) and {seconds:.2f} second(s)"
    return f"{seconds:.2f} second(s)"
