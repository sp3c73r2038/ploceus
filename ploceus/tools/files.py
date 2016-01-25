# -*- coding: utf-8 -*-
import jinja2
import os
from tempfile import mkstemp

from ploceus.runtime import context_manager, env
from ploceus.helper import run, sudo
from ploceus.logger import log


def is_file(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -f %s' % path,
             quiet=True,
             sudo_user=sudo_user, _raise=False).succeeded


def is_dir(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -d %s' % path,
             quiet=True,
             sudo_user=sudo_user, _raise=False).succeeded


def is_symlink(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    return _('test -L %s' % path,
             quiet=True,
             sudo_user=sudo_user, _raise=False).succeeded


def owner(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%U %s' % path,
            quiet=True, sudo_user=sudo_user).stdout.strip()
    return rv


def group(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%G %s' % path,
           quiet=True, sudo_user=sudo_user).stdout.strip()
    return rv


def mode(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('stat -c %%a %s' % path,
           quiet=True, sudo_user=sudo_user).stdout.strip()
    return '0' + rv
_mode = mode


def umask(path, use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    rv = _('umask', quiet=True, sudo_user=sudo_user).stdout.strip()
    return rv


def chown(path, user, grp, recursive=False,
          use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run

    recur = ''
    if recursive:
        recur = '-R'

    return _('chown %s %s:%s %s' % (recur, user, grp, path),
             sudo_user=sudo_user)


def getmtime(path, use_sudo=True):
    _ = (use_sudo and sudo) or run
    return int(_('stat -c %%Y %s' % path, quiet=True).stdout.strip())


def chmod(path, mode, recursive=False,
          use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run

    recur = ''
    if recursive:
        recur = '-R'

    return _('chmod %s %s %s' % (recur, mode, path), sudo_user=sudo_user)


def mkdir(path, user=None, grp=None, mode=None,
          use_sudo=None, sudo_user=None):
    _ = (use_sudo and sudo) or run
    _('mkdir -p %s' % path, sudo_user=sudo_user)

    if (user and (owner(path) != user)) or (grp and (group(path) != grp)):
        chown(dest, user, grp)

    if mode and (mode(path) != mode):
        chmod(dest, mode)


def upload_file(dest, src=None, contents=None,
                user=None, grp=None, mode=None, quiet=False):
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

    if quiet is False:
        log('file: %s -> %s' % (localpath, dest), prefix='upload')

    ssh.sftp.put(localpath, dest)

    if t is not None:
        os.unlink(localpath)

    if (user and (owner(dest) != user)) or (grp and (group(dest) != grp)):
        chown(dest, user, grp)

    if mode and (_mode(dest) != mode):
        chmod(dest, mode)


def upload_template(dest, template=None, contents=None,
                    jinja_ctx=None, user=None, grp=None, mode=None):
    context = context_manager.get_context()
    ssh = context['sshclient']

    jinja_ctx = jinja_ctx or {}
    if 'extra_vars' in context and context['extra_vars']:
        jinja_ctx.update(context['extra_vars'])


    _ctx = context.copy()
    _ctx.pop('sshclient')

    jinja_ctx['context'] = _ctx

    _template = template

    if template is not None:
        assert contents is None
        log('template: %s -> %s' % (template, dest), prefix='upload')
        with open(template) as f:
            t = jinja2.Template(f.read(), keep_trailing_newline=True)
            contents = t.render(**jinja_ctx)
            template = None

    if contents is not None:
        assert template is None
        fd, localpath = mkstemp()
        t = os.fdopen(fd, 'w')
        t.write(contents)
        t.close()
        if _template is None:
            log('template: %s -> %s' % (localpath, dest), prefix='upload')

    upload_file(dest, src=localpath, user=user, grp=grp, mode=mode, quiet=True)
