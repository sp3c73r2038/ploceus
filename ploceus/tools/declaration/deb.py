# -*- coding: utf-8 -*-
from ploceus.colors import blue
from ploceus.logger import log
from ploceus.tools import deb
from ploceus.tools import files
from ploceus.tools import system



def package(pkg, update=False, version=False):
    if deb.is_installed(pkg):
        return

    log('install %s', prefix=blue('deb'))
    deb.install(pkg, update=update, version=version)



def packages(pkgs, update=False):
    map(lambda x: package(x, update=update), pkgs)


def uptodate_index(quiet=True, max_age=3600):
    files.upload_file('/etc/apt/apt.conf.d/15-ploceus-update-stamp',
                      contents="""
APT::Update::Post-Invoke-Success {"touch /var/lib/apt/periodic/ploceus-update-success-stamp 2>/dev/null || true";};
                      """)

    if system.time() - deb.last_update_time() > max_age:
        log('updateing apt index', prefix=blue('deb'))
        deb.update_index(quiet=quiet)
    log('apt index updated', prefix=blue('deb'))


def key(key_id, url):
    if not deb.apt_key_exists(key_id):
        deb.add_apt_key(url)
    log('added apt key "%s"' % key_id, prefix=blue('deb'))


def source(name, uri, distribution, *components, **kwargs)    :
    if 'arch' in kwargs:
        arch = '[arch=%s]' % kwargs.get('arch')

    path = '/etc/apt/sources.list.d/%s.list' % name
    components = ' '.join(components)

    contents = 'deb %s %s %s %s\n' % (arch, uri, distribution, components)
    files.upload_file(path, contents=contents)
    log('added apt repo "%s"' % name, prefix=blue('deb'))
