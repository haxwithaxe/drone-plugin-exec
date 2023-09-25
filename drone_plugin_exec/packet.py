
from datetime import datetime
import io
import json
import time

import nacl.public

from .log import log


STOP_BYTES = b'\0\0\0EOM\0\0\0'


class Packetizeable:

    def to_json(self):
        return json.dumps(dict(self)).encode()

    def __iter__(self):
        copy = {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}
        copy['type'] = self.__class__.__name__
        return iter(copy.items())

    @classmethod
    def isinstance(cls, other):
        if isinstance(other, cls):
            return True
        if isinstance(other, dict):
            return other.get('type') == cls.__name__
        return False


class EmptyPacket(Packetizeable):

    __dataclass_fields__ = {}


class PacketTypes:

    types: list[Packetizeable] = []

    @classmethod
    def register_packet_type(cls, new_type: Packetizeable):
        cls.types.append(new_type)


def packetize(wfile: io.BytesIO, box: nacl.public.Box, data: Packetizeable):
    log.debug('packetize: data: %s', dict(data))
    data = data.to_json()
    # data = box.encrypt(data)
    wfile.writelines([data, b'\n', STOP_BYTES, b'\n'])
    wfile.flush()


def _readlines(rfile: io.BytesIO, box: nacl.public.Box, timeout: int = 60):
    start_time = datetime.now()
    while True:
        for line in rfile:
            if line and line.strip() == STOP_BYTES:
                return
            yield line
            if (start_time - datetime).seconds > timeout:
                raise TimeoutError()
        time.sleep(0.01)


def depacketize(rfile: io.BytesIO, box: nacl.public.Box, timeout: int = 60
                ) -> Packetizeable:
    lines = []
    data = None
    for line in _readlines(rfile, box, timeout):
        if line is None:
            continue
        lines.append(line)
        try:
            data = json.loads(b''.join(lines))
            break
        except json.JSONDecodeError:
            pass
    if not lines:
        return EmptyPacket()
    if not data:
        log.error('Failed to decode json from:\n%s',
                  b'\n'.join(lines).decode())
        # Raise a useful exception
        json.loads(b''.join(lines))
        assert False, 'The above json.loads succeeded but it shouldn\'t have.'
    for cls in PacketTypes.types:
        if cls.isinstance(data):
            return cls(**data)
    return data
