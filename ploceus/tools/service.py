# -*- coding: utf-8 -*-
from ploceus.helper import sudo


def is_running(service):
    # TODO: distro family
    if 'running' in _service(service, 'status'):
        return True
    return False


def start(service):
    _service(service, 'start')


def stop(service):
    _service(service, 'stop')


def restart(service):
    _service(service, 'restart')


def reload(service):
    _service(service, 'reload')


def _service(service, action):
    rv = sudo('service %s %s' % (service, action),
              quiet=True).stdout.strip()
    return rv
