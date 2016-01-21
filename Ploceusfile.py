# -*- coding: utf-8 -*-
from ploceus.api import task
from ploceus.runtime import context_manager

@task
def test():
    ctx = context_manager.get_context()
    print(ctx['extra_vars'])
