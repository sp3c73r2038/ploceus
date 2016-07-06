# -*- coding: utf-8 -*-
from ploceus import ssh
from ploceus.inventory import Inventory


class GlobalStore(object):
    """ploceus global store
    """

    tasks = {}
    inventory = Inventory()

    def add_task(self, task):
        self.tasks[task.name] = task

g = GlobalStore()
