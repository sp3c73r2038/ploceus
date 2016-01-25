# -*- coding: utf-8 -*-
import subprocess

import logging
from ploceus.exceptions import RemoteCommandError
from ploceus.runtime import context_manager, env
from ploceus.logger import log

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


def run(command, quiet=False, _raise=True, *args, **kwargs):
    # TODO: global sudo
    _, stdout, stderr, rc = _run_command(command, quiet, _raise)
    return CommandResult(stdout, stderr, rc)


def sudo(command, quiet=False, _raise=True, sudo_user=None):
    sudo_user = sudo_user or 'root'

    command = 'sudo -u %s -H -i %s' % (sudo_user, command)
    _, stdout, stderr, rc =  _run_command(command, quiet, _raise)
    return CommandResult(stdout, stderr, rc)


def local(command, quiet=False, _raise=True):

    p = subprocess.Popen(command, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=env.cwd)
    stdout, stderr = p.communicate()

    stdout = stdout.decode(env.encoding)
    stderr = stderr.decode(env.encoding)

    if p.returncode != 0:
        if quiet is False:
            for line in stderr.split('\n'):
                log(line.strip(), prefix='err')
        if _raise:
            raise LocalCommandError()

    if quiet is False:
        for line in stdout.split('\n'):
            log(line.strip(), prefix='out')

    return CommandResult(stdout, stderr, p.returncode)


def _run_command(command, quiet=False, _raise=True):
    context = context_manager.get_context()
    client = context['sshclient']
    hostname = context['host_string']

    wrapped_command = command

    if quiet is False:
        log(wrapped_command, prefix='run')

    if env.cwd:
        wrapped_command = 'cd %s && %s' % (env.cwd, command)

    stdin, stdout, stderr, rc = client.exec_command(wrapped_command)


    stdout = stdout.read().decode(env.encoding)
    stderr = stderr.read().decode(env.encoding)

    if rc != 0:
        if quiet is False:
            for line in stderr.split('\n'):
                log(line.strip(), prefix='err')

        if _raise:
            raise RemoteCommandError(stderr)

    if quiet is False:
        for line in stdout.split('\n'):
                log(line.strip(), prefix='out')

    return stdin, stdout, stderr, rc
