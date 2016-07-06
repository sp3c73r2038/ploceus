# -*- coding: utf-8 -*-
import os
import types


def find_ploceusfile():
    for fn in ['Ploceusfile.py', 'ploceusfile.py',
               'Ploceusfile', 'ploceusfile']:
        if not os.path.isfile(fn):
            continue

        if fn.endswith('.py'):
            module_name = fn[:-3]
            ploceusfile_from_module(module_name)
            return fn

        ploceusfile_from_pyfile(fn)
        return fn


def ploceusfile_from_module(module_name):
    __import__(module_name, fromlist=[''])


def ploceusfile_from_pyfile(filename):
    d = types.ModuleType('ploceusfile')
    d.__file__ = filename

    with open(filename) as f:
        exec(compile(f.read(), filename, 'exec'), d.__dict__)
