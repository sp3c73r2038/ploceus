# -*- coding: utf-8 -*-
import threading

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


    def run(self, hostname, extra_vars=None, *args, **kwargs):
        return self._run(hostname, extra_vars, *args, **kwargs)


    def _run(self, hostname, extra_vars, *args, **kwargs):
        context = context_manager.get_context()

        # TODO mask dangers context variables
        extra_vars = extra_vars or {}
        context['extra_vars'] = extra_vars

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
            rv = self.func(*args, **kwargs)
        except:
            import traceback
            traceback.print_exc()

        for f in env.post_task_hooks:
            if callable(f):
                f(context)

        client.close()

        return rv

class TaskRunner(object):

    @staticmethod
    def run_task_with_hosts(task, hosts, parallel=False, **kwargs):
        if parallel:
            TaskRunner.run_task_concurrently(task, hosts, **kwargs)
        else:
            TaskRunner.run_task_single_thread(task, hosts, **kwargs)


    @staticmethod
    def run_task_single_thread(task, hosts, **kwargs):
        for host in hosts:
            task.run(host, **kwargs)


    @staticmethod
    def run_task_concurrently(task, hosts, **kwargs):
        threads = list()
        for host in hosts:

            t = threading.Thread(target=task.run,
                                 args=(host,),
                                 kwargs=kwargs)
            t.start()
            threads.append(t)

        while True:
            for t in threads:
                if t.is_alive():
                    t.join(timeout=1)
                else:
                    threads.remove(t)
                    break

            if len(threads) == 0:
                break
