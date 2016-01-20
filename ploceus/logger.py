# -*- coding: utf-8 -*-
import logging
import sys


logger = logging.getLogger('ploceus')
logger.handlers.clear()
hdl = logging.StreamHandler(sys.stderr)
hdl.setLevel(logging.INFO)
logger.addHandler(hdl)
logger.setLevel(logging.INFO)


def log(message, prefix=''):
    from ploceus.runtime import context_manager
    context = context_manager.get_context()
    hostname = context['host_string']

    _ = '[%s] %s: %s' % (hostname, prefix, message)
    logger.info(_)
