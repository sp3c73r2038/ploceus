# -*- coding: utf-8 -*-
from ploceus.colors import blue
from ploceus.logger import log
from ploceus.tools.service import is_running, start, stop, restart, reload



def started(service):
    if not is_running(service):
        start(service)
    log('%s started' % service, prefix=blue('service'))


def stopped(service):
    if is_running(service):
        stop(service)
    log('%s stopped' % service, prefix=blue('service'))


def restarted(service):
    if is_running(service):
        restart(service)
    else:
        start(service)
    log('%s restarted' % service, prefix=blue('service'))


def reloaded(service):
    reload(service)
    log('%s reloaded' % service, prefix=blue('service'))
