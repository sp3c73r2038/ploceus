# -*- coding: utf-8 -*-
from ploceus.helper import run

def time():
    return int(run('date +%s', quiet=True).stdout.strip())


def cpus():
    return int(run(("cat /proc/cpuinfo | "
                    "grep -P 'processor\t: "
                    "' | wc -l"), quiet=True).stdout.strip())
