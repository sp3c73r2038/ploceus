# -*- coding: utf-8 -*-
from ploceus.tools.service import is_running, start, stop, restart, reload
from ploceus.logger import log


def started(service):
    if not is_running(service):
        start(service)
    log('%s started' % service, prefix='service')


def stopped(service):
    if is_running(service):
        stop(service)
    log('%s stopped' % service, prefix='service')


def restarted(service):
    if is_running(service):
        restart(service)
    else:
        start(service)
    log('%s restarted' % service, prefix='service')


def reloaded(service):
    reload(service)
    log('%s reloaded' % service, prefix='service')
