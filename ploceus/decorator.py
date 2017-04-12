# -*- coding: utf-8 -*-
import ploceus.task

def task(*args, **kwargs):
    invoked = bool(not args or kwargs)
    task_class = kwargs.pop('task_class', ploceus.task.Task)

    if not invoked:
        func, args = args[0], ()

    def wrapper(func):
        return task_class(func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)
