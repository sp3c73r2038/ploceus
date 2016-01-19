# -*- coding: utf-8 -*-
from .exceptions import RemoteCommandError
from .runtime import context_manager

__all__ = ['run', 'sudo']


class CommandResult(object):

    def __init__(self, stdout, stderr, value):
        self.stdout = stdout
        self.stderr = stderr
        self.value = value


    @property
    def failed(self):
        return self.value is not 0


    @property
    def succeeded(self):
        return self.value is 0


def run(command, quiet=False, *args, **kwargs):
    # TODO: global sudo
    _, stdout, stderr, rc = _run_command(command, quiet)
    return CommandResult(stdout, stderr, rc)


def sudo(command, quiet=False, sudo_user=None):
    sudo_user = sudo_user or 'root'

    command = 'sudo -u %s -H -i %s' % (sudo_user, command)
    _, stdout, stderr, rc =  _run_command(command, quiet)
    return CommandResult(stdout, stderr, rc)


def _run_command(command, quiet=False):
    context = context_manager.get_context()
    client = context['sshclient']
    hostname = context['host_string']

    stdin, stdout, stderr, rc = client.exec_command(command)

    if rc != 0:
        if quiet is False:
            for line in stderr:
                print('[%s] %s' % (hostname, line.strip()))

        raise RemoteCommandError()

    if quiet is False:
        for line in stdout:
            print('[%s] %s' % (hostname, line.strip()))

    return stdin, stdout, stderr, rc
