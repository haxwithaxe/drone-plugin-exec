"""A common context state."""

import enum
import pathlib
from dataclasses import dataclass
from typing import Any, Union

from .config import Teardown
from .packet import Packetizeable, PacketTypes
from .script import Script


class Action(enum.Enum):
    """Selection of actions the context is being sent to communicate/preform."""

    SCRIPT = 'script'
    ERROR = 'error'
    SCRIPT_ERROR = 'script-error'
    SUCCESS = 'success'


@dataclass
class Context(Packetizeable):
    """A common context between the target and plugin."""

    action: Union[Action, str]
    checkout: bool = True
    commit: str = None
    error: bool = False
    message: str = None
    output: str = None
    repo_path: Union[pathlib.Path, str] = None
    repo_url: str = None
    script: Script = None
    submodules: bool = None
    teardown: Union[str, Teardown] = Teardown.ON_SUCCESS
    tmp_path: pathlib.Path = None
    type: str = None

    @classmethod
    def isinstance(cls, other: Any) -> bool:
        """Return `True` if `other` is a `Context` dehydrated or not."""
        if isinstance(other, cls):
            return True
        if isinstance(other, dict):
            return other['type'] == cls.__name__
        return False

    def __post_init__(self):
        if isinstance(self.action, str):
            self.action = Action(self.action)
        if isinstance(self.repo_path, str):
            self.repo_path = pathlib.Path(self.repo_path)
        if isinstance(self.script, dict):
            self.script = Script(**self.script)
        if isinstance(self.teardown, str):
            self.teardown = Teardown(self.teardown)
        if isinstance(self.tmp_path, str):
            self.tmp_path = pathlib.Path(self.tmp_path)

    def __iter__(self):
        """Return an iterator ready to be turned into a dict for json."""
        copy = dict(super().__iter__())
        if isinstance(self.action, Action):
            copy['action'] = self.action.value
        if self.repo_path:
            copy['repo_path'] = str(self.repo_path)
        if self.script:
            copy['script'] = dict(self.script)
        if isinstance(self.teardown, Teardown):
            copy['teardown'] = self.teardown.value
        if self.tmp_path:
            copy['tmp_path'] = str(self.tmp_path)
        copy['type'] = self.__class__.__name__
        return iter(copy.items())

    def __repr__(self):
        """Return a comprehensive single line string representation."""
        string = [f'<{self.__class__.__name__} ']
        for key, value in dict(self).items():
            string.append(f'{key}={value}, ')
        return ''.join(string).replace('\n', '\\n')

    def __str__(self):
        """Return a human-friendly string representation."""
        string = [self.__class__.__name__]
        for key, value in dict(self).items():
            if key == 'script':
                value = "\n\t\t".join(str(self.script).split("\n\t"))
            if key == 'output' and self.output:
                lines = value.split("\n")
                if len(lines) > 20:
                    short_lines = []
                    short_lines.extend(lines[:11])
                    short_lines.append('...')
                    short_lines.extend(lines[-10:])
                    lines = short_lines
                value = "\n\t\t".join(lines)
            string.append(f'{key}={value}')
        return '\n\t'.join(string)


PacketTypes.register_packet_type(Context)
