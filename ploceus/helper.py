# -*- coding: utf-8 -*-
import errno
import logging
import os
import fcntl


from ploceus.colors import cyan, green, red
from ploceus.exceptions import LocalCommandError, RemoteCommandError
from ploceus.runtime import context_manager, env
from ploceus.logger import log, logger

__all__ = ['run', 'sudo']



class CommandResult(object):

    def __init__(self, stdout, stderr, exitvalue):
        self.stdout = stdout
        self.stderr = stderr
        self.exitvalue = exitvalue


    def __repr__(self):
        return '<#CommandResult %s>' % self.status()

    def status(self):
        if self.failed:
            return 'failed'
        return 'succeeded'

    @property
    def failed(self):
        return self.exitvalue != 0


    @property
    def succeeded(self):
        return self.exitvalue == 0

    @property
    def ok(self):
        return self.succeeded


def nb_fd_readline(fd):
    """non-blocking readline from fd

    Args:
        fd (int): file descriptor to read from

    Returns:
        string, int: line, status
            status: 0  a new line
            status: -1 not a new line
    """
    line = b''
    while True:
        try:
            _ = os.read(fd, 1)
            line += _
            if _ == b'\n':
                return line, 0
            if _ == b'\r':
                _ = os.read(fd, 1)
                return line, 0
        except OSError as e:
            try:
                if type(e) == BlockingIOError:
                    return line, -1
                else:
                    raise
            except NameError:
                if e.errno == errno.EAGAIN:
                    return line, -1
                else:
                    raise


def run_in_child(cmd):
    """run shell command in child process,
    non-blocking yields output.

    Args:
        cmd (string): command to run

    Returns:
        bytes, bytes, int: stderr, stderr and exit value,
            output would be ``None'',
            exit value should use the last one.

    """
    outr, outw = os.pipe()
    errr, errw = os.pipe()
    pid = os.fork()

    exitvalue = None
    if pid == 0:
        # child
        os.dup2(outw, 1)
        os.dup2(errw, 2)

        os.close(outr)
        os.close(outw)
        os.close(errr)
        os.close(errw)

        os.execl('/bin/bash', 'bash', '-c', cmd)
    else:
        f = fcntl.fcntl(outr, fcntl.F_GETFL)
        fcntl.fcntl(outr, fcntl.F_SETFL, f | os.O_NONBLOCK)
        f = fcntl.fcntl(errr, fcntl.F_GETFL)
        fcntl.fcntl(errr, fcntl.F_SETFL, f | os.O_NONBLOCK)

        outline = b''
        errline = b''
        while True:
            _, s = nb_fd_readline(outr)
            if _ and s == 0:
                outline += _
                yield outline, None, exitvalue
                outline = b''
                continue
            if _ and s == -1:
                outline += _

            _, s = nb_fd_readline(errr)
            if _ and s == 0:
                errline += _
                yield None, errline, exitvalue
                errline = b''
                continue
            if _ and s == -1:
                errline += _

            try:
                _pid, exitvalue = os.waitpid(-1, os.WNOHANG)
            except Exception as e:
                try:
                    if type(e) == ChildProcessError:
                        break
                    else:
                        raise
                except NameError:
                    if e.errno == errno.ECHILD:
                        break
                    else:
                        raise

        outline = b''
        while True:
            _, s = nb_fd_readline(outr)
            if _ and s == 0:
                outline += _
                yield outline, None, exitvalue
                outline = b''
                continue
            if _ and s == -1:
                outline += _
            if not _:
                yield outline, None, exitvalue
                break
        errline = b''
        while True:
            _, s = nb_fd_readline(errr)
            if _ and s == 0:
                errline += _
                yield None, errline, exitvalue
                errline = b''
                continue
            if _ and s == -1:
                errline += _
            if not _:
                yield None, errline, exitvalue
                break


def run(command, quiet=False, _raise=True,
        silence=False, *args, **kwargs):
    # TODO: global sudo

    context = context_manager.get_context()

    _, stdout, stderr, rc = _run_command(
        command, quiet, _raise, silence)
    return CommandResult(stdout, stderr, rc)


def sudo(command, quiet=False, _raise=True,
         sudo_user=None, silence=False):
    sudo_user = sudo_user or 'root'

    command = 'sudo -u %s -H -i %s' % (sudo_user, command)
    return run(command, quiet, _raise, silence)


def local(command, quiet=False, _raise=True, silence=False):

    context = context_manager.get_context()

    wrapped_command = command
    if context.get('cwd'):
        wrapped_command = 'cd %s && %s' % (context.get('cwd'), command)

    if not silence:
        _ = '[%s] %s: %s' % (green('local'), cyan('run'), wrapped_command)
        logger.info(_)

    cwd = context.get('cwd')
    if cwd:
        command = 'cd "%s" && %s' % (cwd, command)

    stdout = []
    stderr = []
    exitvalue = 0
    for outline, errline, exitvalue in run_in_child(command):
        if outline:
            line = outline.decode(env.encoding).strip()
            stdout.append(line)
            if not quiet and not env.keep_quiet:
                _ = '[%s] %s: %s' %\
                    (green('local'), 'stdout', line.strip())
                logger.info(_)
        if errline:
            line = errline.decode(env.encoding).strip()
            stderr.append(line)
            if not quiet and not env.keep_quiet:
                _ = '[%s] %s: %s' %\
                    (green('local'), red('stderr'), line.strip())
                logger.error(_)

    stdout = '\n'.join(stdout)
    stderr = '\n'.join(stderr)

    if exitvalue != 0:
        if _raise:
            raise LocalCommandError(
                'stdout: %s\n\nstderr: %s' % (stdout, stderr))

    return CommandResult(stdout, stderr, exitvalue)


def _run_command(command, quiet=False, _raise=True, silence=False):
    context = context_manager.get_context()
    client = context['sshclient']
    hostname = context['host_string']

    wrapped_command = command

    if context.get('cwd'):
        wrapped_command = 'cd %s && %s' % (context.get('cwd'), command)

    if not silence:
        log(wrapped_command, prefix=cyan('run'))
    stdin, stdout, stderr, rc = client.exec_command(wrapped_command)

    stdout = stdout.read().decode(env.encoding)
    stderr = stderr.read().decode(env.encoding)

    if rc != 0:
        if quiet is False and not env.keep_quiet:
            for line in stderr.split('\n'):
                log(line.strip(), prefix=red('stderr'))

        if _raise:
            raise RemoteCommandError(
                'stdout: %s\n\nstderr: %s' % (stdout, stderr))

    if quiet is False and not env.keep_quiet:
        for line in stdout.split('\n'):
                log(line.strip(), prefix='stdout')

    return stdin, stdout, stderr, rc
