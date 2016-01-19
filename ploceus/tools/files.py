# -*- coding: utf-8 -*-
from ploceus.runtime import context_manager, env
from ploceus.helper import run, sudo


def is_file(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -f %s' % path, sudo_user=sudo_user).succeeded


def is_dir(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -d %s' % path, sudo_user=sudo_user).succeeded


def is_symlink(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -L %s' % path, sudo_user=sudo_user).succeeded


def owner(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    out = _('stat -c %%U %s' % path, quiet=True).stdout.read().strip()
    return out.decode(env.encoding)


def group(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%U %s' % path, quiet=True).stdout.read().strip()
    return out.decode(env.encoding)


def mode(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%a %s' % path, quiet=True).stdout.read().strip()
    return '0' + out.decode(env.encoding)


def umask(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('umask', quiet=True).stdout.read().strip()
    return rv.decode(env.encoding)


def chown(path, user, grp, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('chown %s:%s %s' % (user, grp, path))


def chmod(path, mode, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('chmod %s %s' % (mode, path))


def upload_file(src, dest, user=None, grp=None, mode=None):
    ctx = context_manager.get_context()
    ssh = ctx['sshclient']
    ssh.put_file(src, dest)

    if (user and (owner(dest) != user)) or (grp and (group(dest) != grp)):
        chown(dest, user, grp)

    if mode and (mode(path) != mode):
        chmod(dest, mode)



def upload_template(src, dest, jinja_ctx=None,
                    owner=None, group=None, mode=None):
    raise NotImplementedError()
