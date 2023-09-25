
from contextlib import contextmanager
import io
import os
import pathlib
import socketserver
import subprocess
import time

import nacl.public

from .config import TargetConfig
from .environment import script_environmant, working_dir
from ..context import Action, Context
from .. import keys
from ..packet import depacketize, packetize
from ..log import log
from ..script import Script, StdErr, StdOut


class RequestHandler(socketserver.ForkingMixIn,
                         socketserver.StreamRequestHandler):

    def handle(self):
        self._config.tmp_path_root.mkdir(exist_ok=True)
        log.info('Handling request from %s', self.client_address)
        while not (context := self.receive()):
            time.sleep(0.01)
        if not isinstance(context, Context):
            log.error('Got something unkown: %s\n\n', context)
            return
        if context.action == Action.SCRIPT:
            log.info('Got script: %s\n\n', context.script)
            try:
                with script_environmant(self._config, context) as context:
                    with working_dir(context.script.working_dir):
                        self.run_script(context.script, context)
            except Exception as err:
                context.action = Action.ERROR
                context.error = True
                context.message = ('drone_exec_plugin encountered an '
                                   'unexpected problem: '
                                   f'{err.__class__.__name__} {err}')
                self.send(context)
                log.error('Unexpected error while running a script: %s',
                          context.message, exc_info=err)
                raise err from err
        else:
            log.error('Got a non-script action in initial context: %s',
                      context)
            context.message = f'Expected script context got {context.action}'
            context.error = True
            context.action = Action.ERROR
            self.send(context)

    def receive(self, timeout: int = 60):
        return depacketize(self.rfile, self._box, timeout)

    def send(self, data):
        packetize(self.wfile, self._box, data)

    def send_output(self, script: Script, stdout: io.BytesIO,
                    stderr: io.BytesIO):
        while True:
            out_lines = stdout.readlines()
            err_lines = stderr.readlines()
            if not out_lines and not err_lines:
                break
            log.debug('send_output: stdout: %s, stderr: %s', out_lines, err_lines)
            script.append_output(out_lines, err_lines)
            if out_lines is not None:
                self.send(StdOut(b''.join(out_lines), script.id))
            if err_lines is not None:
                self.send(StdErr(b''.join(err_lines), script.id))

    def run_script(self, script: Script, context: Context):
        log.info('Running script: script.id=%s', script.id)
        script_path = script.to_file()
        cmd = [script.shell, str(script_path.absolute())]
        log.debug('run_script: cmd=%s', cmd)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=script.env or {},
            user=script.user,
            umask=script.umask or -1
        )
        while proc.poll() is None:
            self.send_output(script, proc.stdout, proc.stderr)
        # Finish sending output lines
        self.send_output(script, proc.stdout, proc.stderr)
        script.exit_code = proc.returncode
        if script.exit_code != 0:
            context.action = Action.SCRIPT_ERROR
            context.error = True
            context.message = 'The script exited nonzero'
            log.error('%s: returncode=%s', context.message,
                      context.script.exit_code)
        else:
            log.info('Successfully ran script: script.id=%s', script.id)
            context.action = Action.SUCCESS
        # Just making damn sure they match
        assert context.script.id == script.id
        context.script = script
        log.debug('run_script: responding with context')
        self.send(context)

    @classmethod
    def factory(cls, config: TargetConfig):
        privkey = keys.privkey(config.target_privkey_path)
        plugin_pubkey = keys.pubkey(config.plugin_pubkey)
        box = nacl.public.Box(privkey, plugin_pubkey)

        class RequestHandler(cls):
            _config = config
            _privkey = privkey
            _plugin_pubkey = plugin_pubkey
            _box = box

        return RequestHandler


class Server(socketserver.ForkingTCPServer):
    """Override some server class settings."""

    allow_reuse_address = True


def serve_forever(config: TargetConfig):
    if config.address.startswith('unix://'):
        socket_path = pathlib.Path(config.address[7:])
        if socket_path.exists():
            socket_path.unlink()
        log.info('Serving drone-exec-plugin target at %s', socket_path)
        with socketserver.UnixStreamServer(
            str(socket_path),
            RequestHandler.factory(config)
        ) as server:
            server.serve_forever()
    else:
        log.info('Serving drone-exec-plugin target at %s:%s', config.address,
                 config.port)
        with Server(
            (config.address, config.port),
            RequestHandler.factory(config)
        ) as server:
            log.debug('Serve forever at server.server_address: %s',
                      server.server_address)
            server.serve_forever()
