# -*- coding: utf-8 -*-
from ploceus.colors import cyan
from ploceus.logger import log
from ploceus.tools import files
from ploceus.tools import network



def get_url(url, path, user=None, grp=None, mode=None,
            sha1sum=None, use_sudo=False):

    log('%s -> %s' % (url, path), prefix=cyan('network'))

    if sha1sum and files.is_file(path):
        if sha1sum.lower() == files.sha1sum(path):
            return

    network.download(url, path, use_sudo=use_sudo)

    if (user and user != files.owner(path)) or \
       (grp and grp != files.group(path)):
        files.chown(path, user=user, grp=grp, use_sudo=use_sudo)

    if mode and mode != files.mode(path):
        files.chmod(path, mode, use_sudo=use_sudo)

    # TODO: verify checksum after download?
