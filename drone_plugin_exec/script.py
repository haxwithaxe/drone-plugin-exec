
import base64
import io
import pathlib
import sys
import uuid
from dataclasses import dataclass, field
from typing import Union

from .log import log
from .packet import Packetizeable, PacketTypes


def _debase64(encoded: str):
    if not encoded:
        return encoded
    plain_text = base64.decodebytes(encoded.strip().encode()).decode()
    deescaped = plain_text.replace('\\n', '\n')
    log.debug('debase64: plain text: %s', deescaped.split('\n'))
    return deescaped


def _to_str(text: Union[bytes, str]):
    if isinstance(text, bytes):
        return text.decode()
    return text


@dataclass
class Line(Packetizeable):

    line: bytes
    script_id: str
    _output: io.BytesIO = field(init=False)
    type: str = None

    def print(self):
        if self.line:
            self._output.writelines(self.line)
            if hasattr(self._output, 'flush'):
                self._output.flush()

    def __bool__(self) -> bool:
        return bool(self.line)

    def __iter__(self):
        copy = dict(super().__iter__())
        copy.pop('_output')
        copy['line'] = self.line.decode()
        return iter(copy.items())


class StdOut(Line):

    _output = sys.stdout


PacketTypes.register_packet_type(StdOut)


class StdErr(Line):

    _output = sys.stderr


PacketTypes.register_packet_type(StdErr)


@dataclass
class Script:

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
        if stdout:
            self.stdout.extend(stdout)
        if stderr:
            self.stderr.extend(stderr)

    def ingest_result(self, script_result: 'Script'):
        if script_result.id != self.id:
            raise ValueError('Script.id does not match')
        self.exit_code = script_result.exit_code
        self.stdout = script_result.stdout
        self.stderr = script_result.stderr

    def to_file(self):
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
        body = _debase64(self.body)
        if body and len(body) > 50:
            body = '\\n'.join(body.split('\n'))
            body = f'{body[:50]} ...'
        return f'<Script id={self.id}, shell={self.shell}, body="{body}">'
