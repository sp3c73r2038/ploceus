# -*- coding: utf-8 -*-
import os
from tempfile import mkstemp

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
    out = _('stat -c %%U %s' % path,
            quiet=True, sudo_user=sudo_user).stdout.read().strip()
    return out.decode(env.encoding)


def group(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%U %s' % path,
           quiet=True, sudo_user=sudo_user).stdout.read().strip()
    return out.decode(env.encoding)


def mode(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%a %s' % path,
           quiet=True, sudo_user=sudo_user).stdout.read().strip()
    return '0' + out.decode(env.encoding)


def umask(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('umask', quiet=True, sudo_user=sudo_user).stdout.read().strip()
    return rv.decode(env.encoding)


def chown(path, user, grp, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('chown %s:%s %s' % (user, grp, path), sudo_user=sudo_user)


def chmod(path, mode, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('chmod %s %s' % (mode, path), sudo_user=sudo_user)


def mkdir(path, user=None, group=None, mode=None,
          use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    _('mkdir -p %s' % path, sudo_user=sudo_user)

    if (user and (owner(dest) != user)) or (grp and (group(dest) != grp)):
        chown(dest, user, grp)

    if mode and (mode(path) != mode):
        chmod(dest, mode)


def upload_file(dest, src=None, contents=None, user=None, grp=None, mode=None):
    context = context_manager.get_context()
    ssh = context['sshclient']

    if src:
        assert contents is None
        localpath = src
        t = None

    if contents:
        assert src is None
        fd, localpath = mkstemp()
        t = os.fdopen(fd, 'w')
        t.write(contents)
        t.close()

    ssh.sftp.put(localpath, dest)

    if t is not None:
        os.unlink(localpath)
    if (user and (owner(dest) != user)) or (grp and (group(dest) != grp)):
        chown(dest, user, grp)

    if mode and (mode(path) != mode):
        chmod(dest, mode)


def upload_template(dest, template=None, contents=None,
                    user=None, grp=None, mode=None):
    raise NotImplementedError()
    context = context_manager.get_context()
    ssh = context['sshclient']

    if src:
        assert contents is None
        localpath = src
        t = None

    if contents:
        assert src is None
        fd, localpath = mkstemp()
        t = os.fdopen(fd, 'w')
        t.write(contents)
        t.close()

    upload_file(dest, src=localpath, user=user, grp=grp, mode=mode)
