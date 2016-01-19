# -*- coding: utf-8 -*-
import getpass
import os
import socket

import paramiko


class SSHClient(object):

    def __init__(self):
        self._transport = None
        self._sshconfig = paramiko.SSHConfig()

        self._read_ssh_config()


    def _read_ssh_config(self):
        fn = os.path.expanduser('~/.ssh/config')
        if not os.path.isfile(fn):
            return

        with open(fn) as f:
            self._sshconfig.parse(f)


    def _auto_auth(self, username, identities):
        for identity in identities:
            key = paramiko.RSAKey.from_private_key_file(identity)
            self._transport.auth_publickey(username, key)

            if self._transport.is_authenticated():
                break

        # TODO: agent keys


    def _auth_by_password(self, username, password):
        pass


    def connect(self, hostname, username=None, password=None, port=22):
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
        sock.connect((hostname, port))
        self._transport = paramiko.transport.Transport(sock)
        self._transport.start_client()

        host_sshconfig = self._sshconfig.lookup(hostname)

        if username is None:
            username = getpass.getuser()
            if 'user' in host_sshconfig:
                username = host_sshconfig['user']

        if password is None:
            # TODO: DSA key
            if 'identityfile' in host_sshconfig:
                identity = host_sshconfig['identityfile']
            else:
                identity = '~/.ssh/id_rsa'
            self._auto_auth(username, identity)
        else:
            self._auth_by_password()

        if not self._transport.is_authenticated():
            raise RuntimeError('cannot authenticate')


    def exec_command(self, command, bufsize=-1, timeout=None):
        chan = self._transport.open_session(timeout=timeout)
        chan.settimeout(timeout)
        chan.exec_command(command)
        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('r', bufsize)
        stderr = chan.makefile_stderr('r', bufsize)
        rc = chan.recv_exit_status()
        return stdin, stdout, stderr, rc


    def close(self):
        self._transport.close()
