# -*- coding: utf-8 -*-
import getpass
import logging
import os
import socket

import paramiko

from ploceus.runtime import env

logger = logging.getLogger('ploceus.general')

class SSHClient(object):

    def __init__(self):
        self._connected = False
        self._transport = None
        self._gwTransport = None
        self._sftp = None
        self._sshconfig = paramiko.SSHConfig()

        self._read_ssh_config()


    def _read_ssh_config(self):
        fn = os.path.expanduser('~/.ssh/config')
        if not os.path.isfile(fn):
            return

        with open(fn) as f:
            self._sshconfig.parse(f)


    def _auto_auth(self, transport, username, identities):
        for identity in identities:
            try:
                key = paramiko.RSAKey.from_private_key_file(identity)
                transport.auth_publickey(username, key)
                if transport.is_authenticated():
                    return
            except paramiko.ssh_exception.PasswordRequiredException:
                continue
            except paramiko.ssh_exception.AuthenticationException:
                continue

        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        for key in agent_keys:
            try:
                transport.auth_publickey(username, key)
                if transport.is_authenticated():
                    return
            except paramiko.ssh_exception.AuthenticationException:
                continue


    def _auth_by_password(self, transport, username, password):
        transport.auth_password(username, password)


    @property
    def sftp(self):
        if self._sftp:
            return self._sftp
        self._sftp = paramiko.sftp_client.SFTP.from_transport(
            self._transport)
        return self._sftp

    def connectDirectly(self, hostname, username, password, port):
        sflags = socket.SOCK_STREAM
        if hasattr(socket, 'SOCK_CLOEXEC'):
            sflags |= socket.SOCK_CLOEXEC

        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM | sflags)

        sock.settimeout(env.ssh_timeout)

        logger.debug('connecting to %s:%s' % (hostname, port))

        sock.connect((hostname, port))
        self._transport = paramiko.transport.Transport(sock)
        self._transport.start_client()

        host_sshconfig = self._sshconfig.lookup(hostname)

        if password is None:
            # TODO: DSA key
            if 'identityfile' in host_sshconfig:
                identity = host_sshconfig['identityfile']
            else:
                identity = [os.path.expanduser('~/.ssh/id_rsa')]
            self._auto_auth(self._transport, username, identity)
        else:
            self._auth_by_password(self._transport, username, password)

        if not self._transport.is_authenticated():
            raise RuntimeError(
                ('cannot authenticate when '
                 'connecting to %s@%s') % \
                (username, hostname))

        self._connected = True
        return username


    def connectUsingGateway(self, gateway, hostname, username,
                            password, port):

        host_sshconfig = self._sshconfig.lookup(gateway)

        sflags = socket.SOCK_STREAM
        if hasattr(socket, 'SOCK_CLOEXEC'):
            sflags |= socket.SOCK_CLOEXEC

        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_STREAM | sflags)

        gwUser = username or host_sshconfig.get('user', getpass.getuser())
        gwHost = host_sshconfig['hostname']
        gwPort = int(host_sshconfig.get('port', 22))

        logger.debug('connecting to %s@%s using gateway %s@%s' % (
            username,
            hostname,
            gwUser,
            gwHost,
        ))

        sock.settimeout(env.ssh_timeout)
        sock.connect((gwHost, gwPort))

        self._gwTransport = paramiko.transport.Transport(sock)
        self._gwTransport.start_client()

        if password is None:
            # TODO: DSA key
            if 'identityfile' in host_sshconfig:
                identity = host_sshconfig['identityfile']
            else:
                identity = [os.path.expanduser('~/.ssh/id_rsa')]
            self._auto_auth(self._gwTransport, gwUser, identity)
        else:
            self._auth_by_password(self._gwTransport, gwUser, password)

        if not self._gwTransport.is_authenticated():
            raise RuntimeError(
                ('cannot authenticate when '
                 'connecting to gateway %s@%s') % \
                (gwUser, gateway))

        targetSock = self._gwTransport.open_channel(
            'direct-tcpip',
            dest_addr=(hostname, port),
            src_addr=('127.0.0.1', 0),
        )

        self._transport = paramiko.transport.Transport(targetSock)
        self._transport.start_client()

        if password is None:
            # TODO: DSA key
            if 'identityfile' in host_sshconfig:
                identity = host_sshconfig['identityfile']
            else:
                identity = [os.path.expanduser('~/.ssh/id_rsa')]
            self._auto_auth(self._transport, username, identity)
        else:
            self._auth_by_password(self._transport, username, password)

        if not self._transport.is_authenticated():
            raise RuntimeError(
                ('cannot authenticate when '
                 'connecting to %s@%s') % \
                (username, hostname))

        self._connected = True
        return username


    def connect(self, hostname, username=None,
                password=None, port=None, gateway=None):

        hostConfig = self._sshconfig.lookup(hostname)
        hostname = hostConfig['hostname']

        if username is None:
            username = hostConfig.get('user', getpass.getuser())

        port = port or int(hostConfig.get('port', 22))

        if gateway:
            logger.debug(gateway)

            return self.connectUsingGateway(
                gateway=gateway,
                hostname=hostname,
                username=username,
                password=password,
                port=port,
            )
        else:
            return self.connectDirectly(
                hostname=hostname,
                username=username,
                password=password,
                port=port,
            )

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
        if self._transport:
            self._transport.close()
        if self._gwTransport:
            self._gwTransport.close()
        if self._sftp:
            self._sftp.close()
