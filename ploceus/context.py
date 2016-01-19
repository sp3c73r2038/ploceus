# -*- coding: utf-8 -*-

class Context(dict): pass

# TODO: scope
class ContextManager(object):

    def __init__(self):
        self.context = Context()


    def get_context(self):
        return self.context
