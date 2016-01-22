# -*- coding: utf-8 -*-
from ploceus.utils._collections import ThreadLocalRegistry



class Context(dict): pass

# TODO: scope
class ContextManager(object):

    def __init__(self):
        self.context = ThreadLocalRegistry(lambda : Context())


    def get_context(self):
        return self.context()
