# -*- coding: utf-8 -*-
from .cli import context_manager
from .exceptions import RemoteCommandError


def run(command):
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



def sudo(command, sudo_user='root'):
    context = context_manager.get_context()
    client = context['sshclient']
    hostname = context['host_string']

    command = 'sudo -u %s -H -i %s' % (sudo_user, command)
    stdin, stdout, stderr, rc = client.exec_command(command)

    if rc != 0:
        for line in stderr:
            print('[%s] %s' % (hostname, line.strip()))

        raise RemoteCommandError()

    for line in stdout:
        print('[%s] %s' % (hostname, line.strip()))
