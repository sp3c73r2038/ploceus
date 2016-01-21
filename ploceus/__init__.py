# -*- coding: utf-8 -*-
from . import ssh

class GlobalStore(object):

    tasks = {}

    def add_task(self, task):
        self.tasks[task.name] = task

g = GlobalStore()
