# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os

from ploceus.context import ContextManager
from ploceus.environment import Environment



context_manager = ContextManager()
env = Environment()


def cd(path):
    path = path.replace(' ', '\ ')
    if env.cwd and \
       not path.startswith('/') and \
       not path.startswith('~'):
        new_cwd = os.path.join(env.cwd, path)
    else:
        new_cwd = path

    return _setenv('cwd', new_cwd)


@contextmanager
def _setenv(name, value):
    previous = getattr(env ,name)
    setattr(env, name, value)
    yield
    if previous:
        setattr(env, name, previous)
        return
    setattr(env, name, None)
