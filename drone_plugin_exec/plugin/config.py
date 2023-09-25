
from dataclasses import dataclass, field
import socket
import struct
from typing import Union

import nacl.public


from ..config import Config, ConfigError, RepoType, Teardown


def _get_default_gateway():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as routes:
        for line in routes:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                # If not default route or not RTF_GATEWAY, skip it
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


@dataclass
class PluginConfig(Config):

    checkout: bool = True
    env: dict = field(default_factory=dict)
    plugin_privkey: Union[nacl.public.PrivateKey, str] = None
    repo_path: str = None
    repo_type: RepoType = RepoType.HTTP
    script: str = None
    shell: str = '/bin/bash'
    submodules: bool = False
    target_pubkey: Union[nacl.public.PublicKey, str] = None
    teardown: Union[str, Teardown] = Teardown.ON_SUCCESS
    tmp_path: str = None
    umask: int = -1
    user: str = None

    def __post_init__(self):
        super().__post_init__()
        if not self.address:
            self.address = _get_default_gateway()
        if not self.plugin_privkey:
            raise ConfigError('`plugin_privkey` is required')
        if not self.script:
            raise ConfigError('`script` is required')
        if not self.target_pubkey:
            raise ConfigError('`target_pubkey` is required')
        if isinstance(self.checkout, str):
            self.checkout = self.checkout.lower() == 'true'
        if isinstance(self.repo_type, str):
            self.repo_type = RepoType(self.repo_type)
        if isinstance(self.submodules, str):
            self.submodules = self.submodules.lower() == 'true'
        if isinstance(self.port, str):
            self.port = int(self.port)
        if not isinstance(self.umask, int):
            self.umask = int(self.umask)

    @classmethod
    def from_env(cls, env):
        plugin_privkey = env.pop('PLUGIN_PRIVKEY')
        env['PLUGIN_PRIVKEY'] = '-PLUGIN_PRIVKEY-redacted-'
        default_tmp_path = (f'{env["DRONE_REPO"]}-{env["DRONE_COMMIT"][:8]}-'
                            f'{env["DRONE_BUILD_NUMBER"]}')
        return cls(
            address=env.get('PLUGIN_TARGET_ADDRESS'),
            checkout=env.get('PLUGIN_CHECKOUT', cls.checkout),
            env=env,
            plugin_privkey=plugin_privkey,
            port=env.get('PLUGIN_TARGET_PORT'),
            repo_type=env.get('DRONE_REPO_TYPE', cls.repo_type),
            script=env['PLUGIN_SCRIPT'],
            shell=env.get('PLUGIN_SHELL', cls.shell),
            submodules=env.get('PLUGIN_SUBMODULES', cls.submodules),
            target_pubkey=env['PLUGIN_TARGET_PUBKEY'],
            teardown=env.get('PLUGIN_TEARDOWN', Teardown.ON_SUCCESS),
            tmp_path=env.get('PLUGIN_TMP_PATH', default_tmp_path),
            umask=int(env.get('PLUGIN_UMASK', cls.umask)),
            user=env.get('PLUGIN_USER')
        )
