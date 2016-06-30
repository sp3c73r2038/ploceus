# -*- coding: utf-8 -*-
from ploceus.helper import sudo


def is_running(service):
    # TODO: distro family
    _ = _service(service, 'status')
    if _.succeeded and 'running' in _.stdout.strip().lower():
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
              quiet=False, _raise=False)
    return rv
