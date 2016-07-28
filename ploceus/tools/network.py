# -*- coding: utf-8 -*-
from ploceus.helper import run, sudo


def download(url, dest, use_sudo=False):
    _ = (use_sudo and sudo) or run

    # TODO: fallback to wget, etc...

    _('curl -s %s -o %s' % (url, dest), quiet=True, silence=True)
