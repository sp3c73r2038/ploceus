# -*- coding: utf-8 -*-
from ploceus.context import cd, local_mode
from ploceus.decorator import task
from ploceus.helper import local, run, sudo
from ploceus.task import TaskRunner


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
