"""Script utilities and  representations."""

import base64
import io
import pathlib
import sys
import uuid
from dataclasses import dataclass, field
from typing import Union

from .log import log
from .packet import Packetizeable, PacketTypes


def _debase64(encoded: str) -> str:
    """Coerce a possibly base64 encoded string into plain text."""
    if not encoded:
        return encoded
    plain_text = base64.decodebytes(encoded.strip().encode()).decode()
    deescaped = plain_text.replace('\\n', '\n')
    log.debug('debase64: plain text: %s', deescaped.split('\n'))
    return deescaped


def _to_str(text: Union[bytes, str]) -> str:
    """Coerce bytes or a string to a string."""
    if isinstance(text, bytes):
        return text.decode()
    return text


@dataclass
class Line(Packetizeable):
    """An output line base class."""

    line: bytes
    script_id: str
    _output: io.BytesIO = field(init=False)
    type: str = None

    def print(self):
        """Write the text of this line to the appropriate output."""
        if self.line:
            self._output.writelines(self.line)
            if hasattr(self._output, 'flush'):
                self._output.flush()

    def __bool__(self) -> bool:
        """Mimic the effect of `bool` on the text of the line."""
        return bool(self.line)

    def __iter__(self):
        """Return an iterator ready to be turned into a `dict` for json."""
        copy = dict(super().__iter__())
        copy.pop('_output')
        copy['line'] = self.line.decode()
        return iter(copy.items())


class StdOut(Line):
    """A line of stdout from the script."""

    _output = sys.stdout


PacketTypes.register_packet_type(StdOut)


class StdErr(Line):
    """A line of stderr from the script."""

    _output = sys.stderr


PacketTypes.register_packet_type(StdErr)


@dataclass
class Script:
    """A representation of the script to run."""

    body: str
    env: dict = field(default_factory=dict)
    exit_code: int = None
    id: str = None
    shell: str = '/bin/bash'
    stderr: list[bytes] = field(default_factory=list)
    stdout: list[bytes] = field(default_factory=list)
    tmp_path: pathlib.Path = None
    umask: int = None
    user: str = None
    script_path: pathlib.Path = None
    working_dir: pathlib.Path = None

    def append_output(self, stdout: list[bytes], stderr: list[bytes]):
        """Append to stdout and stderr in unison."""
        if stdout:
            self.stdout.extend(stdout)
        if stderr:
            self.stderr.extend(stderr)

    def to_file(self) -> pathlib.Path:
        """Write this script to a file."""
        if not self.script_path:
            self.script_path = self.tmp_path.joinpath(f'script-{self.id}.sh')
        plain_text_body = _debase64(self.body)
        log.debug('script: plain text body: %s', plain_text_body)
        self.script_path.write_text(plain_text_body)
        return self.script_path

    def __post__init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex
        if isinstance(self.tmp_path, str):
            self.tmp_path = pathlib.Path(self.tmp_path)

    def __iter__(self):
        copy = {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}
        copy.pop('script_path')
        if self.tmp_path:
            copy['tmp_path'] = str(self.tmp_path)
        if self.env:
            copy['env'] = dict(self.env)
        if self.working_dir:
            copy['working_dir'] = str(self.working_dir)
        copy['stdout'] = [_to_str(s) for s in self.stdout]
        copy['stderr'] = [_to_str(s) for s in self.stderr]
        return iter(copy.items())

    def __repr__(self):
        attrs = dict(self)
        body = attrs.pop('body')
        string = ['<Script ']
        for key, value in attrs.items():
            string.append(f'{key}={value}, ')
        string.append(f'body="{body}">')
        return ''.join(string)

    def __str__(self):
        """Return a  human-friendly representation of this object."""
        body = _debase64(self.body)
        if body and len(body) > 50:
            body = '\\n'.join(body.split('\n'))
            body = f'{body[:50]} ...'
        return f'<Script id={self.id}, shell={self.shell}, body="{body}">'
