# -*- coding: utf-8 -*-
import ploceus.task


def task(*args, **kwargs):
    invoked = bool(not args or kwargs)
    task_class = kwargs.pop('task_class', ploceus.task.Task)

    if not invoked:
        func, args = args[0], ()

    def wrapper(func):

        def new_func(*_args, **_kwargs):
            rv = func(*_args, **_kwargs)
            return rv

        new_func.__name__ = func.__name__
        new_func.__module__ = func.__module__

        return task_class(new_func, *args, **kwargs)

    return wrapper if invoked else wrapper(func)
