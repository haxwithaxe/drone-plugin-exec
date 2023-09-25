
from datetime import datetime
import io
import socket

import nacl.public

from .config import PluginConfig
from ..context import Action, Context
from .. import keys
from ..packet import depacketize, EmptyPacket, packetize, Packetizeable
from ..log import log, log_every_factory, LogLevel
from ..script import StdErr, StdOut


class Client:

    def __init__(self, config: PluginConfig):
        self._config = config
        self._privkey = keys.privkey(config.plugin_privkey)
        self._target_pubkey = keys.pubkey(config.target_pubkey)
        self._box = nacl.public.Box(self._privkey, self._target_pubkey)
        self._sock: socket.socket = None
        self._rfile: io.BytesIO = None
        self._wfile: io.BytesIO = None
        log.debug('New Client: %s', self)

    def __enter__(self) -> 'Client':
        log.debug('Entering Client context')
        if self._config.address.startswith('unix://'):
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.connect(self._config.address[7:])
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self._config.address, self._config.port))
        self._rfile = self._sock.makefile('rb')
        self._wfile = self._sock.makefile('wb')

    def __exit__(self, *args):
        log.debug('Exiting Client context')
        self._sock.close()

    def send(self, data: Packetizeable):
        packetize(self._wfile, self._box, data)

    def receive(self, timeout: int = 60) -> Packetizeable:
        return depacketize(self._rfile, self._box, timeout)

    def send_script(self, context: Context):
        log.debug('send_script start: %s', context.script)
        context.action = Action.SCRIPT
        self.send(context)
        log.info('Remote output:')
        received = self.handle_output(context)
        log.debug('send_script end: %s', received)
        return received

    def handle_output(self, context: Context, timeout: int = 60,
                      receive_timeout: int = 60):
        start_time = datetime.now()
        log_every = log_every_factory(LogLevel.DEBUG)
        combined_output = []
        while True:
            log_every('handling output', inclued_time=True)
            try:
                data = self.receive(receive_timeout)
            except TimeoutError:
                continue
            log.debug('handle_output: Got data: %s', data)
            if not data:
                continue
            if isinstance(data, StdOut):
                assert data.script_id == context.script.id
                combined_output.append(data.line)
                data.print()
            elif isinstance(data, StdErr):
                assert data.script_id == context.script.id
                combined_output.append(data.line)
                data.print()
            elif isinstance(data, Context):
                log.debug('handle_output: context.action=%s, '
                          'context.script.id=%s',
                          data.action, data.script.id)
                if data.action == Action.SUCCESS:
                    data.output = ''.join(combined_output)
                    return data
                elif data.action == Action.SCRIPT_ERROR:
                    log.error('Script exited nonzero: context=%s', data)
                elif data.action == Action.ERROR:
                    log.error('Got remote error running script: context=%s',
                              data)
                else:
                    log.error('Got unexpected Context while handling output: '
                              'context=%s', data)
                data.output = ''.join(combined_output)
                return data
            elif isinstance(data, EmptyPacket):
                log.debug('Got empty packet: %s', data)
            else:
                log.error('Got unexpected data: "%s"', data)
                continue
            if (datetime.now() - start_time).seconds > timeout:
                raise TimeoutError(f'{timeout} seconds elapsed while handling '
                                   'output from the command: '
                                   f'{context.script.id}')
