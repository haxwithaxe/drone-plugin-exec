"""Logging utilities."""

import contextlib
import enum
import logging
from datetime import datetime
from typing import Union


class LogLevel(enum.Enum):
    """Log levels and utils for converting between them."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

    @classmethod
    def cast(cls, level: Union[int, str, 'LogLevel']) -> 'LogLevel':
        """Cast a log level representation to a `LogLevel`."""
        if isinstance(level, cls):
            return cls
        if isinstance(level, int):
            for level_enum in cls:
                if getattr(logging, level_enum.value) == level:
                    return level_enum
        if isinstance(level, str):
            with contextlib.suppress(AttributeError):
                return cls(level)
        raise ValueError(f'Invalid `LogLevel` "{level}"')

    def __int__(self) -> int:
        """Return a `logging` log level equivalent."""
        return getattr(logging, self.value)

    def __str__(self) -> str:
        """Return a string equivalent."""
        return self.value


logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(name='drone-exec-plugin')


class _Tick:
    """A stateful object for tracking tick/tock mode."""

    def __init__(self):  # noqa: 105
        self._tock = False

    def tick(self):
        """Set tick mode."""
        self._tock = False

    def tock(self):
        """Set tock mode."""
        self._tock = True

    def __bool__(self) -> bool:
        """Return `True` if this is in "tick" mode."""
        return not self._tock


def __fuzzy_mod(numerator: int, denominator: int, fuzzyness: int):
    """Fuzzy modulo.

    Arguments:
        numerator: The numerator (top/left number).
        denominator: The denominator (bottom/right number).
        fuzzyness: The number to subtract from the numerator for the minimum
            and add to the numerator for the maximum.
    """
    start = numerator - fuzzyness
    if start < 1:
        start = 1
    mods = []
    for numer in range(start, numerator+fuzzyness):
        mods.append(numer % denominator)
    return mods


def log_every_factory(level: LogLevel, interval: int = 20,
                      fuzzyness: int = 10):
    """Return a function that logs about every `interval`."""
    tick = _Tick()
    log_func = getattr(log, level.value.lower())
    start_time = datetime.now()

    def log_every(message: str, *args, include_time=True, **kwargs):
        now = datetime.now()
        mods = __fuzzy_mod(int(start_time.timestamp()), int(now.timestamp()),
                           fuzzyness)
        if tick and 0 not in mods:
            if include_time:
                log_func(message, now.isoformat(), *args, **kwargs)
            else:
                log_func(message, *args, **kwargs)
            tick.tock()
        if 0 in mods:
            tick.tick()

    return log_every
