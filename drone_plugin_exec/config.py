
import enum
from dataclasses import dataclass
from typing import Union


class ConfigError(Exception):
    pass


class RepoType(enum.Enum):

    SSH = 'ssh'
    HTTP = 'http'


class Teardown(enum.Enum):

    ALWAYS = 'always'
    ON_SUCCESS = 'on-success'
    NEVER = 'never'


@dataclass
class Config:

    address: str = None
    port: str = 44274
    teardown: Union[str, Teardown] = Teardown.ON_SUCCESS

    def __post_init__(self):
        self.teardown = Teardown(self.teardown)

    def __iter__(self):
        copy = {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}
        copy['type'] = self.__class__.__name__
        return iter(copy.items())

    def __repr__(self):
        attrs = dict(self)
        string = [f'<{self.__class__.__name__} ']
        for key, value in attrs.items():
            string.append(f'{key}={value}, ')
        return ''.join(string)

    def __str__(self):
        string = [self.__class__.__name__]
        for key, value in dict(self).items():
            string.append(f'{key}={value}')
        return '\n\t'.join(string)
