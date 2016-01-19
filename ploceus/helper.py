# -*- coding: utf-8 -*-
from .exceptions import RemoteCommandError
from .runtime import context_manager

__all__ = ['run', 'sudo']


class CommandResult(object):

    def __init__(self, value):
        self.value = value


    @property
    def failed(self):
        return self.value is not 0


    @property
    def succeeded(self):
        return self.value is 0



def run(command, *args, **kwargs):
    # TODO: global sudo
    _, _, _, rc = _run_command(command)
    return CommandResult(rc)


def sudo(command, sudo_user=None):
    sudo_user = sudo_user or 'root'

    command = 'sudo -u %s -H -i %s' % (sudo_user, command)
    _, _, _, rc =  _run_command(command)
    return CommandResult(rc)


def _run_command(command):
    context = context_manager.get_context()
    client = context['sshclient']
    hostname = context['host_string']

    stdin, stdout, stderr, rc = client.exec_command(command)

    if rc != 0:
        for line in stderr:
            print('[%s] %s' % (hostname, line.strip()))

        raise RemoteCommandError()

    for line in stdout:
        print('[%s] %s' % (hostname, line.strip()))

    return stdin, stdout, stderr, rc
