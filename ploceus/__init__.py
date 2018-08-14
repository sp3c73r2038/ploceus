# -*- coding: utf-8 -*-
from ploceus.inventory import Inventory


class GlobalStore(object):
    """ploceus global store
    """

    tasks = {}
    inventory = Inventory()

    def add_task(self, task):
        self.tasks[task.name] = task


# 2018-08-14
# deprecated 不使用全局变量
g = GlobalStore()


def setup():
    g.inventory.setup()
