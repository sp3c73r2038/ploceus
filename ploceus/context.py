# -*- coding: utf-8 -*-
from contextlib import contextmanager
import os

from ploceus.utils._collections import ThreadLocalRegistry


class Context(dict):

    def __init__(self, *args, **kwargs):
        self.sshclient = None
        super().__init__(*args, **kwargs)

    def get_client(self):

        if not self.sshclient._connected:

            username = self['username']
            hostname = self['host_string']
            password = self['password']

            from ploceus.runtime import env
            gateway = env.gateway_settings.get(hostname)

            username = self.sshclient.connect(
                hostname,
                username=username,
                password=password,
                gateway=gateway)

            self['username'] = username

        return self.sshclient


def new_context():
    rv = Context()
    rv['extra_vars'] = {}
    return rv


# TODO: scope
class ContextManager(object):

    def __init__(self):
        # self.context = ThreadLocalRegistry(new_context)
        pass

    def get_context(self):
        from ploceus.runtime import env
        ctx = env.getCurrentCtx()
        return ctx.taskCtx


def cd(path):

    from ploceus.runtime import context_manager
    context = context_manager.get_context()

    path = path.replace(' ', '\ ')
    if 'cwd' in context and \
       not path.startswith('/') and \
       not path.startswith('~'):
        new_cwd = os.path.join(context['cwd'], path)
    else:
        new_cwd = path

    return _setenv('cwd', new_cwd)


@contextmanager
def _setenv(name, value):

    from ploceus.runtime import context_manager
    context = context_manager.get_context()

    previous = context.get(name)
    context[name] = value
    err = None
    try:
        yield
    except Exception as e:
        err = e

    if previous:
        context[name] = previous
    else:
        context[name] = None

    if err is not None:
        raise err
