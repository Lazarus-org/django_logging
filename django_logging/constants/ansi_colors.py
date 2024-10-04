from dataclasses import dataclass


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class AnsiColors:
    BLACK: str = "\033[0;30m"
    RED: str = "\033[0;31m"
    GREEN: str = "\033[0;32m"
    YELLOW: str = "\033[0;33m"
    BLUE: str = "\033[0;34m"
    MAGENTA: str = "\033[0;35m"
    CYAN: str = "\033[0;36m"
    GRAY: str = "\033[0;37m"
    WHITE: str = "\033[0;38m"
    RESET: str = "\033[0m"
    BRIGHT_BLACK: str = "\033[0;90m"
    BRIGHT_RED: str = "\033[0;91m"
    BRIGHT_GREEN: str = "\033[0;92m"
    BRIGHT_YELLOW: str = "\033[0;93m"
    BRIGHT_BLUE: str = "\033[0;94m"
    BRIGHT_MAGENTA: str = "\033[0;95m"
    BRIGHT_CYAN: str = "\033[0;96m"
    BRIGHT_WHITE: str = "\033[0;97m"
    PINK: str = "\033[38;5;213m"
    LIGHT_PURPLE = "\033[38;5;129m"
    BLACK_BACKGROUND: str = "\033[40m"
    RED_BACKGROUND: str = "\033[41m"
    GREEN_BACKGROUND: str = "\033[42m"
    YELLOW_BACKGROUND: str = "\033[43m"
    BLUE_BACKGROUND: str = "\033[44m"
    MAGENTA_BACKGROUND: str = "\033[45m"
    CYAN_BACKGROUND: str = "\033[46m"
    WHITE_BACKGROUND: str = "\033[47m"
    BRIGHT_BLACK_BACKGROUND: str = "\033[100m"
    BRIGHT_RED_BACKGROUND: str = "\033[101m"
    BRIGHT_GREEN_BACKGROUND: str = "\033[102m"
    BRIGHT_YELLOW_BACKGROUND: str = "\033[103m"
    BRIGHT_BLUE_BACKGROUND: str = "\033[104m"
    BRIGHT_MAGENTA_BACKGROUND: str = "\033[105m"
    BRIGHT_CYAN_BACKGROUND: str = "\033[106m"
    BRIGHT_WHITE_BACKGROUND: str = "\033[107m"

    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"
    ITALIC: str = "\033[3m"
    BOLD_ITALIC: str = "\033[1;3m"
    UNDERLINE: str = "\033[4m"
    BLINK: str = "\033[5m"
    INVERT: str = "\033[7m"
    STRIKETHROUGH: str = "\033[9m"


# Mapping log levels to ANSI colors
LOG_LEVEL_COLORS = {
    "DEBUG": AnsiColors.BLUE,
    "INFO": AnsiColors.GREEN,
    "WARNING": AnsiColors.YELLOW,
    "ERROR": AnsiColors.RED,
    "CRITICAL": AnsiColors.RED_BACKGROUND,
}
