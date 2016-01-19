# -*- coding: utf-8 -*-
from . import exceptions
from .cli import cmdr, context_manager
from .ssh import SSHClient



class Task(object):

    def __init__(self, func):
        self.func = func

        module = func.__module__
        if module.lower() == 'ploceusfile':
            module = ''
        name = func.__name__
        if module:
            name = '%s.%s' % (module, name)
        self.name = name

        cmdr.add_task(self)


    def run(self, hostname):
        return self._run(hostname)


    def _run(self, hostname):
        # TODO: hooks
        context = context_manager.get_context()

        # connect to remote host
        client = SSHClient()
        client.connect(hostname)

        # setting context
        context['sshclient'] = client
        context['host_string'] = hostname

        rv = None
        try:
            rv = self.func()
        except exceptions.RemoteCommandError as err:
            print('\n\n\terror when running remote command\n')
        except:
            import traceback
            traceback.print_exc()

        client.close()

        return rv
