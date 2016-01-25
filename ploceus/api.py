# -*- coding: utf-8 -*-
from ploceus.decorator import task
from ploceus.helper import local, run, sudo
from ploceus.runtime import cd


def run_task_by_group(group_name, task, extra_vars=None):
    from ploceus import g
    g.inventory.find_inventory()
    group = g.inventory.get_target_hosts(group_name)
    hosts = group['hosts']
    extra_vars = extra_vars or {}
    if 'vars' in group:
        extra_vars.update(group['vars'])
    for host in hosts:
        task.run(host, extra_vars)
