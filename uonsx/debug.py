from __future__ import annotations

from uonsx.util import colorize


class Debug:
    def __init__(self, debug_level: int = 0):
        self.debug = True if debug_level > 0 else False
        self.debug_level = debug_level

    def __bool__(self):
        return self.debug

    def __int__(self):
        return self.debug_level

    def __str__(self):
        return f"debug level: {self.debug_level}"

    def print(self, debug_level: int = 0, msg: str = "") -> None:
        if self.debug_level >= debug_level:
            print(colorize(f"DEBUG[{debug_level}]: {msg}", "blue"))
