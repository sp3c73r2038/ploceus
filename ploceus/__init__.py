# -*- coding: utf-8 -*-
import logging
import os

from ploceus.inventory import Inventory
from ploceus.logger import logger


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

    debug = os.environ.get('PLOCEUS_DEBUG')
    if debug:
        logger.setLevel(logging.DEBUG)
        for h in logger.handlers:
            h.setLevel(logging.DEBUG)
