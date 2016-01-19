## Ploceus

Ploceus is inspired by Fabric and Ansible, but with plain Python code.

Ploceus is powered by paramiko.

`Ploceusfile.py` or `Ploceusfile`

```
# -*- coding: utf-8 -*-
from ploceus.api import task
from ploceus.api import run, sudo

@task
def test():
    run('date')
    sudo('id')
```

list tasks.

```
$ ve ploceus -l
```

run tasks with hosts.

```
$ ve ploceus -H example.com test
```


## License

GPL-2

## note

ve - https://github.com/erning/ve
