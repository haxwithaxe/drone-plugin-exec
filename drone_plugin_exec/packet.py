"""Common packeization utilities."""

import io
import json
import time
from datetime import datetime
from typing import Generator

import nacl.public

from .log import log

STOP_BYTES = b'\0\0\0\23\23\23\0\0\0'
_STOP_BUFFER = [chr(b).encode() for b in list(STOP_BYTES)]


class Packetizeable:
    """A base class for packetizable types."""

    def to_json(self):
        """Return a json representation of this object."""
        return json.dumps(dict(self)).encode()

    def __iter__(self):
        """Return an iterator ready to be turned into a `dict` for json."""
        copy = {k: getattr(self, k) for k in self.__dataclass_fields__.keys()}
        copy['type'] = self.__class__.__name__
        return iter(copy.items())

    @classmethod
    def isinstance(cls, other):
        """Return `True` if `other` is a member, dehydrated or not."""
        if isinstance(other, cls):
            return True
        if isinstance(other, dict):
            return other.get('type') == cls.__name__
        return False


class EmptyPacket(Packetizeable):
    """Represents an empty packet."""

    __dataclass_fields__ = {}


class PacketTypes:
    """A registry of packet types."""

    types: list[Packetizeable] = []

    @classmethod
    def register_packet_type(cls, new_type: Packetizeable):
        """Register a new packet type."""
        cls.types.append(new_type)


def packetize(wfile: io.BytesIO, box: nacl.public.Box, data: Packetizeable):
    """Format and transmit a packet."""
    log.debug('packetize: data: %s', dict(data))
    data = data.to_json()
    data = box.encrypt(data)
    sent_bytes = wfile.write(data)
    sent_bytes += wfile.write(STOP_BYTES)
    wfile.flush()
    log.debug('sent bytes: %s', sent_bytes)


def _read_until_ETB(rfile: io.BytesIO, box: nacl.public.Box, timeout: int = 60
                    ) -> Generator[bytes, None, None]:
    """Return a generator of decrypted bytes until the ETB is found."""
    start_time = datetime.now()
    while True:
        stop_buffer = []
        data = []
        while byte := rfile.read(1):
            stop_buffer.append(byte)
            if len(stop_buffer) > len(STOP_BYTES):
                data.append(stop_buffer.pop(0))
            if stop_buffer == _STOP_BUFFER:
                stop_buffer = []
                payload = b''.join(data)
                data = []
                yield box.decrypt(payload)
            if timeout and (datetime.now() - start_time).seconds > timeout:
                raise TimeoutError()
        time.sleep(0.01)


def depacketize(rfile: io.BytesIO, box: nacl.public.Box, timeout: int = 60
                ) -> Packetizeable:
    """Return a received, decrypted, and assembled packet.

    If a packet cannot be found in the data the data is returned unassembled.
    If no data is received a `EmptyPacket` is returned.

    Raises:
        json.JSONDecodeError: When data is received but isn't decodable as
            JSON.
    """
    lines = []
    data = None
    for line in _read_until_ETB(rfile, box, timeout):
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
                  b'\n'.join(lines).decode(errors='ignore'))
        # Raise a useful exception
        json.loads(box.decrypt(b''.join(lines)))
        raise AssertionError('The above json.loads succeeded but it '
                             'shouldn\'t have.')
    for cls in PacketTypes.types:
        if cls.isinstance(data):
            return cls(**data)
    return data
