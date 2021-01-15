# -*- coding: utf-8 -*-
from collections import defaultdict
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

    options = {}
    if username:
        options['username'] = username
    if password:
        options['password'] = password

    results = []
    for task in tasks:
        pool = ThreadPoolExecutor(max_workers=concurrency)
        tracking = []

        for conn in hosts:
            if isinstance(conn, str):
                conn = {
                    'name': conn,
                    'connection': conn
                }
            # entry from cli will be a Task instance
            # otherwise, just wrap it with a new Task
            if not isinstance(task, Task):
                task = Task(task)

            future = pool.submit(
                execute, task, conn,
                kwargs=kwargs,
                extra_vars=extra_vars,
                **options,
            )
            tracking.append(future)

            # FIXME: sleep is only useful in pool, not here
            if sleep:
                time.sleep(sleep)

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
            rt.sshclient = None

    rv = results
    # FIXME: legacy code is buggy!
    buggyResult = {x.hostname: x for x in rv}
    rv = ExecuteResult()
    rv.update(buggyResult)

    rv.result = defaultdict(dict)
    for rt in results:
        if isinstance(rt.task, Task):
            name = rt.task.name
        else:
            name = rt.task.__name__
        taskName = rt.task.__module__ + '.' + name
        rv.result[rt.hostname][taskName] = rt
    rv.result = dict(rv.result)

    te = time.time()
    if os.environ.get('LOG_TIMECOST'):
        processResult(rv, te - ts)

    return rv

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


def execute(task, conn, **options):
    # import pprint
    # pprint.pprint("===========")
    # pprint.pprint(options)
    # pprint.pprint("===========")
    extra_vars = options.pop('extra_vars', {})
    kwargs = options.pop('kwargs', {})
    username = options.pop('username', task.ssh_user)
    password = options.pop('password', None)
    port = options.pop('ssh_port', task.ssh_port)

    context = new_context()

    hostname = conn['connection']
    if '@' in hostname:
        _, hostname = hostname.split('@', maxsplit=1)
        if not username:
            username = _

    if ':' in hostname:
        hostname, port = hostname.split(':', 1)
        port = int(port)

    # prepare context
    context['connection'] = conn['connection']  # 2021-01-15
    context['password'] = password
    context['username'] = username
    context['host_string'] = hostname
    context['_hostname'] = conn['name']
    context['ssh_port'] = port
    context['ssh_keyfile'] = conn.get('ssh_keyfile')
    context['ssh_passphrase'] = conn.get('ssh_passphrase')
    # import pprint
    # pprint.pprint("===========")
    # pprint.pprint(context)
    # pprint.pprint("===========")

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

    rv.task = task
    rv.timecost = te - ts

    # 2021-01-14 human readable hostname without
    # user, password, port
    rv.hostname = context['_hostname']
    rv.conn = conn

    if sshclient:
        rv.sshclient = sshclient

    # ugly hack for non-breaking usage
    if os.environ.get('LOG_TIMECOST'):
        log(color.yellow('task {} timecost: {:.3f}s').format(
            task.name, rv.timecost))

    return rv


class ExecuteResult(dict):
    """

    for compatibility purpose, (rather wrong) result will be accessible
    through dict API, e.g. result['hostname'], result.get('hostname')
    """

    def __init__(self):
        self.result = None

    def get_result(self, hostname, taskName):
        """
        result is nested like

        {
          'hostname': {
            'taskName': ...
          }
        }

        taskName can be retrieve by
        (task or func).__module__ + '.' + (task or func).__name__
        """
        rv = self.result.get('hostname')
        if rv is None:
            return rv
        return rv.get(taskName)
