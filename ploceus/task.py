# -*- coding: utf-8 -*-
from ploceus import g
from ploceus import exceptions
from ploceus.runtime import context_manager, env
from ploceus.ssh import SSHClient


class Task(object):

    def __init__(self, func, ssh_user=None):
        self.func = func
        self.ssh_user = ssh_user

        module = func.__module__
        if module.lower() == 'ploceusfile':
            module = ''
        name = func.__name__
        if module:
            name = '%s.%s' % (module, name)
        self.name = name

        g.add_task(self)


    def run(self, hostname):
        return self._run(hostname)


    def _run(self, hostname):

        context = context_manager.get_context()

        # connect to remote host
        client = SSHClient()

        username = client.connect(hostname, username=self.ssh_user)

        # setting context
        context['sshclient'] = client
        context['host_string'] = hostname
        context['username'] = username

        for f in env.pre_task_hooks:
            if callable(f):
                f(context)

        rv = None
        try:
            rv = self.func()
        except exceptions.RemoteCommandError as err:
            print('\n\n\terror when running remote command\n')
        except:
            import traceback
            traceback.print_exc()

        for f in env.post_task_hooks:
            if callable(f):
                f(context)

        client.close()

        return rv
