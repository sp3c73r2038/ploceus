# -*- coding: utf-8 -*-
import time

from ploceus import g
from ploceus.exceptions import ArgumentError, PloceusError
from ploceus.inventory import Inventory
from ploceus.runtime import context_manager
from ploceus.ssh import SSHClient

def group_task(tasks, group, inventory=None,
               sleep=None, parallel=None,
               ssh_user=None, ssh_pwd=None,
               extra_vars=None, **kwargs):
    """Programmable interface for running tasks by host groups specified
    in inventory file. This function is  intended to be used by any 3rd-party
    Python code only.

    Args:
        tasks (list[ploceus.task.Task]): task list or a single task.
        group (str): hosts group name
        inventory (str): path to inventory file/directory
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
    if g.inventory.empty:
        raise ArgumentError('cannot find inventory.')
    group_hosts = g.inventory.get_target_hosts(group)
    return run_task(
        tasks, group_hosts['hosts'],
        sleep=sleep,
        parallel=parallel,
        ssh_user=ssh_user,
        ssh_pwd=ssh_pwd,
        extra_vars=extra_vars,
        **kwargs)


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

            if not username:
                username = task.ssh_user

            if '@' in hostname:
                _, hostname = hostname.split('@', maxsplit=1)
                if not username:
                    username = _

            # setting context
            context['password'] = password
            context['username'] = username
            context['host_string'] = hostname

            client = SSHClient()
            runner.append_ssh_client(client)
            context.sshclient = client

            # ansible like host_vars
            extra_vars = extra_vars or {}
            extra_vars.update(
                g.inventory.get_target_host(hostname))

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
