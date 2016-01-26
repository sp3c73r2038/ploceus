# -*- coding: utf-8 -*-
import logging
import sys

from ploceus.runtime import context_manager


logger = logging.getLogger('ploceus')
logger.handlers.clear()
hdl = logging.StreamHandler(sys.stderr)
hdl.setLevel(logging.INFO)
logger.addHandler(hdl)
logger.setLevel(logging.INFO)


def log(message, prefix=''):
    from ploceus.runtime import context_manager

    context = context_manager.get_context()

    if 'local_mode' in context and context.get('local_mode'):
        hostname = 'local'
    else:
        context = context_manager.get_context()
        hostname = context['host_string']


    _ = '[%s] %s: %s' % (hostname, prefix, message)
    logger.info(_)
