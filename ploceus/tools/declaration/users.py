# -*- coding: utf-8 -*-
from ploceus.tools import users
from ploceus.tools.declaration import files

def user(name, uid, gid,
         shell=None, home=None,
         groups=None, system=None,
         mode='0700'):

    if users.exists(name):
        users.modify_user(name, uid=uid, gid=gid,
                          shell=shell, home=home,
                          groups=groups)
    else:
        users.create_user(name, uid=uid, gid=gid,
                          shell=shell, home=home,
                          groups=groups, system=system)

    # ensure home directory exists, permission and mode.
    files.directory(home, user=name, mode=mode, use_sudo=True)
