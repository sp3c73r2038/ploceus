# -*- coding: utf-8 -*-
from ploceus.utils._collections import ScopedRegistry
from ploceus.context import Context

from _thread import get_ident


class Environment(object):

    pre_task_hooks = []
    post_task_hooks = []

    # 2018-08-14
    setup_hooks = []
    # not implemented yet
    teardown_hooks = []

    encoding = 'utf-8'
    cwd = None
    ssh_timeout = 5
    break_on_error = True
    keep_quiet = False

    # default to current working directory
    template_path = ''

    # ssh connecting gateway
    gateway_settings = {}

    # global setting ssh private keys
    # element structure:
    # (${keyType}, ${path}, ${passphrase})
    # example:
    # no passphrase
    # ('rsa', '~/.ssh/some/id_rsa', '')
    # with passphrase
    # ('ed25519', '~/.ssh/another/id_ed25519', 'somepass')
    ssh_pkeys = []

    def __init__(self):
        self.scope = ScopedRegistry(
            ExecutorContext, get_ident)

    def getCurrentCtx(self):
        return self.scope()


class ExecutorContext(object):

    def __init__(self):
        self.taskCtx = Context()
        self.duty = None
