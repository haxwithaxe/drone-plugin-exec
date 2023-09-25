
from contextlib import contextmanager
import os
import pathlib
import shutil
import tempfile

import git

from .config import TargetConfig
from ..config import ConfigError, Teardown
from ..context import Context
from ..log import log


def setup(config: TargetConfig, context: Context) -> Context:
    log.debug('Setup running environment: %s', config.tmp_path_root)
    if not context.tmp_path:
        context.tmp_path = pathlib.Path(tempfile.mkdtemp(
            dir=config.tmp_path_root
        ))
    if context.tmp_path.is_absolute():
        if not context.tmp_path.is_relative_to(config.tmp_path_root):
            raise ConfigError(
                f'The `tmp_path` ({context.tmp_path}) in the `Context` is not '
                'a subdirectory of the configured `tmp_path_root` '
                f'({config.tmp_path_root})'
            )
    else:
        context.tmp_path = config.tmp_path_root.joinpath(context.tmp_path)
    config.tmp_path_root.mkdir(exist_ok=True)
    context.tmp_path.parent.mkdir(exist_ok=True)
    context.tmp_path.mkdir(exist_ok=True)
    if context.checkout and not context.repo_path:
        context.repo_path = context.tmp_path.joinpath('repo')
    elif context.checkout and not context.repo_path.is_absolute():
        context.repo_path = context.tmp_path.joinpath(context.repo_path)
    if not context.script.tmp_path:
        context.script.tmp_path = context.repo_path or context.tmp_path
    if not context.script.working_dir:
        context.script.working_dir = (context.repo_path or
                                      context.script.tmp_path)
    if context.checkout:
        checkout(context)
    return context


def checkout(context: Context):
    log.info('Checkout the repo %s to %s', context.repo_url, context.repo_path)
    repo = git.Repo.clone_from(context.repo_url, context.repo_path)
    repo.index.reset(context.commit)
    if context.submodules:
        log.info('Updating submodules recursively')
        repo.submodule_update()


def teardown(config: TargetConfig, context: Context):
    # Verify the path given is in the configured tmp path root
    assert context.tmp_path.absolute().is_relative_to(config.tmp_path_root)
    shutil.rmtree(context.tmp_path)


@contextmanager
def script_environmant(config: TargetConfig, context: Context):
    context = setup(config, context)
    try:
        yield context
    finally:
        if config.teardown == Teardown.NEVER:
            return
        if config.teardown == Teardown.ALWAYS or not context.error:
            teardown(config, context)


@contextmanager
def working_dir(path: pathlib.Path):
    original_dir = os.curdir
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(original_dir)
