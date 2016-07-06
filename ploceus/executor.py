# -*- coding: utf-8 -*-
import time

from ploceus.ssh import SSHClient
from ploceus.exceptions import PloceusError
from ploceus.runtime import context_manager

def run_task(tasks, hosts,
             sleep=None, parallel=None,
             ssh_user=None, ssh_pwd=None,
             extra_vars=None, **kwargs):
    """Programmable interface for running tasks,
    could be used by any 3rd-party Python code or plocues itself.

    Args:
        tasks (list[ploceus.task.Task]): task list or a single task.
        hosts (list[str]): hosts FQDN name or set in ``hosts'' file.
        sleep (int): interval between two tasks when not in parallel mode,
            in seconds
        parallel (bool): whether run tasks in parallel fashion. ** [not
            supported yet] **
        ssh_user (str): username to use when connecting ssh, will override
            username in task's property, sshconfig and hostname
        ssh_pwd (str): password to use when connecting ssh, will override
            password in sshconfig
        extra_vars (dict): additional variables which be inserted into context
        **kwargs (dict): keyword arguments will pass to decorated function
    """
    # TODO:
    if parallel:
        raise PloceusError('parallel mode no implemented yet.')

    rv = {}
    runner = TaskRunner()
    username = None
    password = None

    if type(tasks) != list:
        tasks = [tasks]

    if ssh_user:
        username = ssh_user
    if ssh_pwd:
        password = ssh_pwd

    for task in tasks:
        for host in hosts:
            context = context_manager.get_context()
            hostname = host
            # connect to remote host
            client = SSHClient()

            if not username:
                username = task.ssh_user

            if '@' in hostname:
                _, hostname = hostname.split('@', maxsplit=1)
                if not username:
                    username = _

            username = client.connect(
                hostname, username=username,
                password=password)

            # setting context
            context['sshclient'] = client
            context['host_string'] = hostname
            context['username'] = username
            runner.append_ssh_client(client)

            rv[hostname] = task.run(extra_vars=extra_vars, **kwargs)

        if sleep:
            time.sleep(sleep)

    runner.dispose_ssh_clients()
    return rv


class TaskRunner(object):
    """runner to carry out a task
    """

    ssh_clients = []

    def append_ssh_client(self, client):
        """register ssh client to TaskRunner

        Args:
            client (ploceus.ssh.SSHClient): client to record
        """
        self.ssh_clients.append(client)


    def dispose_ssh_clients(self):
        """close all ssh clients registered.
        """
        for c in self.ssh_clients:
            c.close()

        del self.ssh_clients[:]
