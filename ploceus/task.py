# -*- coding: utf-8 -*-
import threading
import time

from ploceus import g
from ploceus import exceptions
from ploceus.runtime import context_manager, env
from ploceus.ssh import SSHClient


def run_task_by_host(hostname, tasks,
                     extra_vars=None, **kwargs):
    from ploceus import g
    hosts = [hostname]
    extra_vars = extra_vars or {}

    if type(tasks) != list:
        tasks = [tasks]

    for task in tasks:
        TaskRunner.run_task_with_hosts(task, hosts,
                                       extra_vars=extra_vars,
                                       **kwargs)


def run_task_by_group(group_name, tasks,
                      extra_vars=None, parallel=False, **kwargs):
    from ploceus import g
    g.inventory.find_inventory()
    group = g.inventory.get_target_hosts(group_name)
    hosts = group['hosts']
    extra_vars = extra_vars or {}
    if 'vars' in group:
        extra_vars.update(group['vars'])

    if type(tasks) != list:
        tasks = [tasks]

    for task in tasks:
        TaskRunner.run_task_with_hosts(task, hosts,
                                       parallel=parallel,
                                       extra_vars=extra_vars,
                                       **kwargs)



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


    def __repr__(self):
        return '<ploceus.task.Task %s>' % self.name


    def __str__(self):
        return '<ploceus.task.Task %s>' % self.name


    def run(self, hostname, extra_vars=None, *args, **kwargs):
        return self._run(hostname, extra_vars, *args, **kwargs)


    def _run(self, hostname, extra_vars, *args, **kwargs):
        context = context_manager.get_context()

        # TODO mask dangers context variables
        extra_vars = extra_vars or {}
        context['extra_vars'] = extra_vars

        # ansible like host_vars
        context['extra_vars'].update(
            g.inventory.get_target_host(hostname))

        # connect to remote host
        client = SSHClient()

        password = None
        if 'password' in kwargs:
            password = kwargs.pop('password')
        username = client.connect(hostname, username=self.ssh_user,
                                  password=password)

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
    def run_task_with_hosts(task, hosts, parallel=False,
                            sleep=0, password=None, **kwargs):

        if parallel:
            TaskRunner.run_task_concurrently(task, hosts,
                                             password=password, **kwargs)
        else:
            TaskRunner.run_task_single_thread(task, hosts,
                                              sleep=sleep,
                                              password=password, **kwargs)


    @staticmethod
    def run_task_single_thread(task, hosts, sleep=0, password=None, **kwargs):
        if hosts is None:
            return

        for host in hosts:
            task.run(host, password=password, **kwargs)
            if sleep:
                time.sleep(sleep)


    @staticmethod
    def run_task_concurrently(task, hosts, password=None, **kwargs):
        if hosts is None:
            return

        threads = list()

        def thread_wrapper(task, host, password, **kwargs):
            try:
                task.run(host, password=password, **kwargs)
            except:
                print('error when running task: %s, host: %s, kwargs: %s' %
                      (task, host, kwargs))
                raise

        for host in hosts:

            t = threading.Thread(target=thread_wrapper,
                                 args=(task, host, password, ),
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
