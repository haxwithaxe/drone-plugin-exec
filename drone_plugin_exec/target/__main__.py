# noqa: D100

import pathlib

import typer

from ..log import LogLevel, log
from . import daemon
from .config import TargetConfig

app = typer.Typer()


@app.command()
def main(config: pathlib.Path = typer.Option(),
         log_level: LogLevel = typer.Option(LogLevel.ERROR.value)):
    """The entrypoint for the target side of the plugin."""  # noqa: D401
    log.setLevel(int(log_level))
    conf = TargetConfig.from_path(config)
    log.debug('Running target at %s:%s', conf.address, conf.port)
    daemon.serve_forever(conf)


if __name__ == '__main__':
    app()
