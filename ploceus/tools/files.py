# -*- coding: utf-8 -*-
from ploceus.runtime import context_manager
from ploceus.helper import run, sudo


def is_file(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -f %s' % path, sudo_user=sudo_user).succeeded


def upload_file(src, dest, owner=None, group=None, mode=None):
    ctx = context_manager.get_context()
    ssh = ctx['sshclient']
    ssh.put_file(src, dest)

    # TODO: checks


def upload_template(src, dest, jinja_ctx=None,
                    owner=None, group=None, mode=None):
    raise NotImplementedError()
