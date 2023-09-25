
import pathlib

import typer

from . import daemon
from .config import TargetConfig
from ..log import log, LogLevel


app = typer.Typer()


@app.command()
def main(config: pathlib.Path = typer.Option(),
         log_level: LogLevel = typer.Option(LogLevel.ERROR.value)):
    log.setLevel(int(log_level))
    conf = TargetConfig.from_path(config)
    log.debug('Running target at %s:%s', conf.address, conf.port)
    daemon.serve_forever(conf)


if __name__ == '__main__':
    app()
