# -*- coding: utf-8 -*-
from ploceus.helper import run

def time():
    return int(run('date +%s', quiet=True).stdout.read().strip())
