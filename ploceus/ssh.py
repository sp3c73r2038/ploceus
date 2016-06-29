# -*- coding: utf-8 -*-
import getpass
import os
import socket

import paramiko


class SSHClient(object):

    def __init__(self):
        self._transport = None
        self._sftp = None
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
            try:
                key = paramiko.RSAKey.from_private_key_file(identity)
                self._transport.auth_publickey(username, key)
                if self._transport.is_authenticated():
                    return
            except paramiko.ssh_exception.PasswordRequiredException:
                continue

        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        for key in agent_keys:
            try:
                self._transport.auth_publickey(username, key)
                if self._transport.is_authenticated():
                    return
            except paramiko.ssh_exception.AuthenticationException:
                continue


    def _auth_by_password(self, username, password):
        self._transport.auth_password(username, password)


    @property
    def sftp(self):
        if self._sftp:
            return self._sftp
        self._sftp = paramiko.sftp_client.SFTP.from_transport(self._transport)
        return self._sftp


    def connect(self, hostname, username=None, password=None, port=22):

        sflags = socket.SOCK_STREAM
        if hasattr(socket, 'SOCK_CLOEXEC'):
            sflags |= socket.SOCK_CLOEXEC

        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM | sflags)


        host_sshconfig = self._sshconfig.lookup(hostname)
        if 'port' in host_sshconfig:
            port = int(host_sshconfig['port'])

        sock.connect((hostname, port))
        self._transport = paramiko.transport.Transport(sock)
        self._transport.start_client()



        if username is None:
            username = getpass.getuser()
            if 'user' in host_sshconfig:
                username = host_sshconfig['user']

        if password is None:
            # TODO: DSA key
            if 'identityfile' in host_sshconfig:
                identity = host_sshconfig['identityfile']
            else:
                identity = [os.path.expanduser('~/.ssh/id_rsa')]
            self._auto_auth(username, identity)
        else:
            self._auth_by_password(username, password)

        if not self._transport.is_authenticated():
            raise RuntimeError('cannot authenticate')

        return username


    def exec_command(self, command, bufsize=-1, timeout=None, get_pty=True):
        chan = self._transport.open_session(timeout=timeout)
        if get_pty:
            chan.get_pty()
        chan.settimeout(timeout)
        chan.exec_command(command)
        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('r', bufsize)
        stderr = chan.makefile_stderr('r', bufsize)
        rc = chan.recv_exit_status()
        return stdin, stdout, stderr, rc


    def put_file(self, src, dest):
        self.sftp.put(src, dest)


    def get_file(self, src, dest):
        self.sftp.get(src, dest)


    def close(self):
        self._transport.close()
        if self._sftp:
            self._sftp.close()
