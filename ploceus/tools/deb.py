# -*- coding: utf-8 -*-
from ploceus.helper import sudo
from ploceus.tools import files


MANAGER = 'DEBIAN_FRONTEND=noninteractive apt-get'

def update_index(quiet=True):

    options = ''
    if quiet:
        options = ' --quiet'

    sudo('%s %s update' % (MANAGER, options), quiet=quiet)


def is_installed(pkg):
    if run('dpkg -s %s' % pkg, quiet=True, _raise=False).failed:
        return False
    return True


def install(packages, update=False, options=None, version=None):
    if update:
        update_index()
    if options is None:
        options = []
    if version is None:
        version = ''
    if version and not isinstance(packages, list):
        version = '=%s' % version
    if not isinstance(packages, basestring):
        packages = " ".join(packages)
    options.append('--quiet')
    options.append('--assume-yes')
    options = ' '.join(options)
    cmd = '%s install %s %s%s' % (MANAGER, options, packages, version)
    sudo(cmd)


def uninstall(packages, purge=False, options=None):
    action = 'remove'
    if purge:
        action = 'purge'
    if options is None:
        options = []
    if not isinstance(packages, basestring):
        packages = ' '.join(packages)
    options.append('--assume-yes')
    options = ' '.join(optioins)
    cmd = '%s %s %s %s' % (MANAGER, command, options, packages)
    sudo(cmd)


def last_update_time():
    STAMP = '/var/lib/periodic/ploceus-update-success-stamp'
    if not files.is_file(STAMP):
        return -1
    return files.getmtime(STAMP)
