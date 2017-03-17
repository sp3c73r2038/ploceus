# -*- coding: utf-8 -*-

class Environment(object):
    pre_task_hooks = []
    post_task_hooks = []
    encoding='utf-8'
    cwd = None
    ssh_timeout = 5
    break_on_error = True
    keep_quiet = False

    # default to current working directory
    template_path = ''
