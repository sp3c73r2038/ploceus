# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
import os
import time

import terminaltables

from ploceus import g
from ploceus import colors as color
from ploceus.context import get_current_scope, new_context
from ploceus.exceptions import ArgumentError, PloceusError
from ploceus.runtime import context_manager, env
from ploceus.logger import log
import ploceus.runtime as runtime
from ploceus.ssh import SSHClient
from ploceus.task import Task


def group_task(tasks, group, inventory=None,
               sleep=None, parallel=None,
               ssh_user=None, ssh_pwd=None,
               extra_vars=None, cli_options=None,
               concurrency=None, **kwargs):
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
        cli_options=cli_options,
        concurrency=concurrency,
        **kwargs)


def run_task(tasks, hosts,
             sleep=None, parallel=None,
             ssh_user=None, ssh_pwd=None,
             extra_vars=None, cli_options=None,
             concurrency=None, **kwargs):
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
        concurrency (int): max concurrency for parallel executing
        **kwargs (dict): keyword arguments will pass to decorated function
    """
    username = None
    password = None

    if not isinstance(hosts, list):
        raise RuntimeError('hosts should be a list')

    if type(tasks) != list:
        tasks = [tasks]

    if ssh_user:
        username = ssh_user
    if ssh_pwd:
        password = ssh_pwd

    if not cli_options:
        cli_options = {}

    if not extra_vars:
        extra_vars = {}

    # FIXME: 定义钩子参数
    for f in runtime.env.setup_hooks:
        f(cli_options=cli_options)

    if not concurrency:
        concurrency = os.cpu_count()

    if not parallel:
        concurrency = 1

    ts = time.time()

    for task in tasks:
        pool = ThreadPoolExecutor(max_workers=concurrency)
        tracking = []

        for host in hosts:
            # entry from cli will be a Task instance
            # otherwise, just wrap it with a new Task
            if not isinstance(task, Task):
                task = Task(task)

            future = pool.submit(
                execute, task, host,
                    kwargs=kwargs,
                    extra_vars=extra_vars,
                    username=username,
                    password=password,
            )
            tracking.append(future)

            if sleep:
                time.sleep(sleep)

        results = []
        pool.shutdown(wait=True)
        for future in tracking:
            if future.done():
                result = future.result()
                results.append(result)
                continue
            if not future.running():
                ex = future.exception()
                results.append(ex)

    # close all ssh client connections
    for rt in results:
        if rt.sshclient:
            rt.sshclient.close()

    rv = results
    # FIXME: legacy code is buggy!
    buggyResult = {x.hostname: x for x in rv}

    te = time.time()
    if os.environ.get('LOG_TIMECOST'):
        processResult(buggyResult, te - ts)

    return buggyResult


def processResult(results, realTime):
    # FIXME: buggy result
    title = 'execution result'

    tableData = [['Hostname', 'Result OK', 'timecost(s)']]

    print('')
    print('')
    totalTimecost = 0
    for hostname, result in results.items():
        c = color.green
        s = 'OK'
        if not result.ok:
            c = color.red
            s = 'NG'
        row = [c(x) for x in [hostname, s, '{:.3f}'.format(result.timecost)]]
        totalTimecost += result.timecost
        tableData.append(row)
    table = terminaltables.AsciiTable(tableData, title)

    lines = table.table.split('\n')
    indent = 8
    out = '\n'.join([' ' * indent + x for x in lines])
    print(out)

    print('')
    print(' ' * indent + 'total timecost: {:.3f}s'.format(totalTimecost))
    print(' ' * indent + ' real timecost: {:.3f}s'.format(realTime))
    print(' ' * indent + 'speed up: {:.1f}x'.format(
        totalTimecost / realTime))
    print('')
    print('')


def execute(task, hostname, **options):
    extra_vars = options.pop('extra_vars', {})
    kwargs = options.pop('kwargs', {})
    username = options.pop('username', task.ssh_user)
    password = options.pop('password', None)


    context = new_context()

    if '@' in hostname:
        _, hostname = hostname.split('@', maxsplit=1)
        if not username:
            username = _

    # prepare context
    context['password'] = password
    context['username'] = username
    context['host_string'] = hostname

    sshclient = None
    if not task.local_mode:
        # local task will not need SSH connection
        sshclient = SSHClient()
        context.sshclient = sshclient

    # ansible like host_vars
    extra_vars.update(
        g.inventory.get_target_host(hostname))

    scope = get_current_scope()
    scope.push(context)
    ts = time.time()
    rv = task.run(extra_vars=extra_vars, **kwargs)
    te = time.time()
    context = scope.pop()

    rv.hostname = hostname
    rv.timecost = te - ts
    if sshclient:
        rv.sshclient = sshclient

    # ugly hack for non-breaking usage
    if os.environ.get('LOG_TIMECOST'):
        log(color.yellow('task {} timecost: {:.3f}s').format(
            task.name, rv.timecost))

    return rv
