
from dataclasses import dataclass
import pathlib

import docker
try:
    import tomllib
except ModuleNotFoundError:
    import toml as tomllib

from ..config import Config, ConfigError
from ..log import log


@dataclass
class TargetConfig(Config):

    plugin_pubkey: bytes = None
    target_privkey_path: pathlib.Path = None
    docker_network: str = None
    docker_uri: str = None
    tmp_path_root: pathlib.Path = pathlib.Path('/tmp/drone-plugin-exec-target')

    def __post_init__(self):
        super().__post_init__()
        if not self.plugin_pubkey:
            raise ConfigError('`plugin_pubkey` is required.')
        if not self.target_privkey_path:
            raise ConfigError('`target_privkey_path` is required.')
        self.target_privkey_path = pathlib.Path(
            self.target_privkey_path
        )
        self.tmp_path_root = pathlib.Path(self.tmp_path_root)
        if self.docker_network and not self.address:
            self._set_address_from_docker_net()

    def _set_address_from_docker_net(self):
        if not self.docker_uri:
            client = docker.from_env()
        else:
            client = docker.DockerClient(self.docker_uri)
        net = client.networks.get(self.docker_network)
        net_config = net.attrs['IPAM']['Config']
        gateways = [n['Gateway'] for n in net_config if n['Gateway']]
        self.address = gateways.pop()
        log.info('Set listen address to "%s" from docker network "%s"',
                 self.address, self.docker_network)

    @classmethod
    def from_path(cls, config_path: pathlib.Path):
        log.info('Loading config from "%s"', config_path)
        config = tomllib.loads(config_path.read_text())
        return cls(
            **config
        )
