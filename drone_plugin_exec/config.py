"""Common configuration utilities."""

import enum
from dataclasses import dataclass
from typing import Union


class ConfigError(Exception):
    """Indicate an error in the configuration."""


class RepoType(enum.Enum):
    """Selections for types of repository URLs."""

    SSH = 'ssh'
    HTTP = 'http'


class Teardown(enum.Enum):
    """Selections for whether and when to tear down the runtime environment."""

    ALWAYS = 'always'
    ON_SUCCESS = 'on-success'
    NEVER = 'never'


@dataclass
class Config:
    """A base configuration class."""

    address: str = None
    """The target side listen address."""
    port: str = None
    """The target side listen port."""
    teardown: Union[str, Teardown] = Teardown.ON_SUCCESS
    """Whether and when to teardown the runtime environment."""

    def __post_init__(self):
        self.teardown = Teardown(self.teardown)

    def __iter__(self):
        """Return an iterator ready to be turned into a `dict`."""
        copy = {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}
        copy['type'] = self.__class__.__name__
        return iter(copy.items())

    def __repr__(self):
        """Return a comprehensive single line string representation."""
        attrs = dict(self)
        string = [f'<{self.__class__.__name__} ']
        for key, value in attrs.items():
            string.append(f'{key}={value}, ')
        return ''.join(string).replace('\n', '\\n')

    def __str__(self):
        """Return a human-friendly string representation."""
        string = [self.__class__.__name__]
        for key, value in dict(self).items():
            string.append(f'{key}={value}')
        return '\n\t'.join(string)
