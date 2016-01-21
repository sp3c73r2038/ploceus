# -*- coding: utf-8 -*-
from ploceus.tools import deb
from ploceus.tools import files
from ploceus.tools import system
from ploceus.logger import log


def package(pkg, update=False, version=False):
    if deb.is_installed(pkg):
        return

    log('install %s', prefix='deb')
    deb.install(pkg, update=update, version=version)



def packages(pkgs, update=False):
    map(lambda x: package(x, update=update), pkgs)


def uptodate_index(quiet=True, max_age=3600):
    files.upload_file('/etc/apt/apt.conf.d/15-ploceus-update-stamp',
                      contents="""
APT::Update::Post-Invoke-Success {"touch /var/lib/apt/periodic/ploceus-update-success-stamp 2>/dev/null || true";};
                      """)

    if system.time() - deb.last_update_time() > max_age:
        log('updateing apt index', prefix='deb')
        deb.update_index(quiet=quiet)
    log('apt index updated', prefix='deb')
