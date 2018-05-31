# -*- coding: utf-8 -*-
import binascii
import getpass
import logging
from os.path import expanduser, isfile
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
        fn = expanduser('~/.ssh/config')
        if not isfile(fn):
            return

        with open(fn) as f:
            self._sshconfig.parse(f)

    def _get_local_pkey_paths(self):
        pkey_fns = {'id_rsa', 'id_ed25519'}
        pkey_paths = []
        for f in pkey_fns:
            path = expanduser('~/.ssh/%s' % f)
            if isfile(path):
                pkey_paths.append(path)

        return pkey_paths

    def _auto_auth(self, transport, username, config):
        # 0x0 IdentifyFile in ssh_config
        if 'identityfile' in config:
            idents = config['identityfile']
            for ident in idents:
                logger.debug('ident: {}'.format(ident))
                cls = paramiko.rsakey.RSAKey
                if ident.lower() == 'rsa':
                    cls = paramiko.rsakey.RSAKey
                elif ident.lower() == 'dsa':
                    cls = paramiko.dsskey.DSSKey
                elif ident.lower() == 'ed25519':
                    cls = paramiko.ed25519key.Ed25519Key
                key = cls.from_private_key_file(ident)
                if self._auth_by_key(transport, username, key):
                    return

        # 0x1 env.ssh_pkeys
        if env.ssh_pkeys:
            for ktype, path, passphrase in env.ssh_pkeys:
                path = expanduser(path)
                if ktype.lower() == 'rsa':
                    cls = paramiko.rsakey.RSAKey
                elif ktype.lower() == 'dsa':
                    cls = paramiko.dsskey.DSSKey
                elif ktype.lower() == 'ed25519':
                    cls = paramiko.ed25519key.Ed25519Key
                else:
                    msg = 'unsupported keytype {}'.format(ktype)
                    raise ValueError(msg)
                key = cls.from_private_key_file(path, passphrase)
                if self._auth_by_key(transport, username, key):
                    return

        # 0x2 agent keys
        agent = paramiko.Agent()
        for key in agent.get_keys():
            if self._auth_by_key(transport, username, key):
                return

        # 0x3 frequently used keys
        # id_rsa
        path = expanduser('~/.ssh/id_rsa')
        if isfile(path):
            try:
                key = paramiko.rsakey.RSAKey.from_private_key_file(path)
                if self._auth_by_key(transport, username, key):
                    return
            except paramiko.ssh_exception.PasswordRequiredException:
                pass

        # id_dsa
        path = expanduser('~/.ssh/id_dsa')
        if isfile(path):
            try:
                key = paramiko.dsskey.DSSKey.from_private_key_file(path)
                if self._auth_by_key(transport, username, key):
                    return
            except paramiko.ssh_exception.PasswordRequiredException:
                pass

        # id_ed25519
        path = expanduser('~/.ssh/id_ed25519')
        if isfile(path):
            try:
                key = paramiko.ed25519key.Ed25519Key.from_private_key_file(
                    path)
                if self._auth_by_key(transport, username, key):
                    return
            except paramiko.ssh_exception.PasswordRequiredException:
                pass

        # maybe still not authenticated yet?

    def _auth_by_key(self, transport, username, key):
        """
        return True if authenticated
        """
        rv = False
        fp = binascii.hexlify(key.get_fingerprint())
        logger.debug('auth using key: {}'.format(fp.decode()))
        try:
            transport.auth_publickey(username, key)
            if transport.is_authenticated():
                rv = True
        except paramiko.ssh_exception.AuthenticationException:
            pass
        return rv

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
            self._auto_auth(self._transport, username, host_sshconfig)
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
            self._auto_auth(self._gwTransport, gwUser, host_sshconfig)
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

        # FIXME: pkeys via gateway?

        if password is None:
            self._auto_auth(self._transport, username, host_sshconfig)
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
