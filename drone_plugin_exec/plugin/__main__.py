
import base64
import logging
import os
import sys

from ..context import Action, Context
from ..log import log
from ..script import Script
from . import sender
from .config import PluginConfig, RepoType


def main():
    log.setLevel(getattr(logging, os.environ.get('PLUGIN_LOG_LEVEL', 'ERROR')))
    config = PluginConfig.from_env(os.environ)
    log.debug('main: config: %s', config)
    script_id = (f"{os.environ['DRONE_COMMIT'][:8]}-"
                 f"{os.environ['DRONE_BUILD_NUMBER']}")
    script_body = base64.encodebytes(config.script.encode())
    script = Script(id=script_id, body=script_body.decode(), env=config.env,
                    shell=config.shell, umask=config.umask, user=config.user)
    log.debug('main: script: %s', script)
    repo_url = config.env['DRONE_GIT_HTTP_URL']
    if config.repo_type == RepoType.SSH:
        repo_url = config.env['DRONE_GIT_SSH_URL']
    context = Context(
        action=Action.SCRIPT,
        checkout=config.checkout,
        commit=config.env['DRONE_COMMIT'],
        repo_url=repo_url,
        submodules=config.submodules,
        tmp_path=config.tmp_path,
        script=script,
        repo_path=config.repo_path
    )
    log.debug('main: context: %s', context)
    runner = sender.Client(config)
    with runner:
        received_context = runner.send_script(context)
    if received_context.error:
        log.error('Remote error: %s', received_context.message)
        sys.exit(1)
    log.info('Success: %s', received_context.message or script.id)


if __name__ == '__main__':
    main()
