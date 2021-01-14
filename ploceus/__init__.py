# -*- coding: utf-8 -*-
import logging
import os

import coloredlogs

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

    debug = os.environ.get('PLOCEUS_DEBUG')
    import pprint
    pprint.pprint("DEBUG: {}".format(debug))
    if debug:
        logger = logging.getLogger("ploceus")
        fmt = (
            '[%(asctime)s %(levelname)7s (%(process)d) '
            '<%(name)s> %(filename)s:%(lineno)d] ---\n%(message)s\n')
        coloredlogs.install(fmt=fmt, level=logging.DEBUG, logger=logger)
        # f = logging.Formatter(fmt)
        # logger.setLevel(logging.DEBUG)
        # for h in logger.handlers:
        #     h.setFormatter(f)
        #     h.setLevel(logging.DEBUG)

    g.inventory.setup()
