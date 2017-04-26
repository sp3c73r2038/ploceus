# -*- coding: utf-8 -*-
import argparse
import sys

from ploceus import g
from ploceus import ploceusfile
from ploceus.exceptions import ArgumentError
from ploceus.executor import run_task
from ploceus.inventory import Inventory
from ploceus.runtime import env

class Ploceus(object):

    def __init__(self):
        self.ploceusfile = None
        self.hosts = []
        self.task_name = None
        self.group = None
        self.parallel = False
        self.sleep = 0
        self.disable_pubkey = False
        self.password = None

    def run(self):

        ap = argparse.ArgumentParser()
        ap.add_argument(
            '-l', '--list-tasks', action='store_true',
            help='list all avaiable tasks')
        ap.add_argument(
            '-I', '--list-inventory', action='store_true',
            help='list all avaiable groups of hosts'
        )
        ap.add_argument(
            '-f', '--ploceus-file', help='speicify Ploceusfile')
        ap.add_argument(
            '-H', '--host', action='append', help='specify target host',
            default=[])
        ap.add_argument(
            '-i', '--inventory', help='specify inventory file/directory')
        ap.add_argument(
            '-g', '--group', help='specify hosts group')
        ap.add_argument(
            '-P', '--parallel', action='store_true',
            help='run task across hosts parallelly'
        )
        ap.add_argument(
            '-s', '--sleep', default=0, type=int,
            help='sleep between two hosts'
        )
        ap.add_argument(
            '-k', '--disable-pubkey',
            action='store_true',
            help='do not use pubkey to authenticate'
        )
        ap.add_argument(
            '-p', '--password', help='use password to connect'
        )
        ap.add_argument(
            '-q', '--quiet', help='quiet mode, suppress command output',
            action='store_true'
        )
        ap.add_argument(
            '--args', help='arguments passing to task',
            action='append', default=[],
        )
        ap.add_argument(
            'task_name', nargs='?',
            help='task name to carry out')

        options = ap.parse_args()
        # print(options)

        ploceus_filename = options.ploceus_file
        if options.ploceus_file is None:
            ploceus_filename = ploceusfile.find_ploceusfile()
        else:
            ploceusfile.ploceusfile_from_pyfile(options.ploceus_file)

        if options.list_tasks:
            self.list_tasks()
            return 1

        g.inventory = Inventory(options.inventory)
        g.inventory.setup()

        if options.list_inventory:
            if g.inventory.empty:
                raise ArgumentError('cannot find inventory.')
            self.list_inventory()
            return 1

        if options.group and g.inventory.empty:
            raise ArgumentError(
                'Specify inventory when using group, please.')

        hosts = options.host or []
        extra_vars = None
        if options.group:
            group_hosts = g.inventory.get_target_hosts(options.group)
            if group_hosts:
                hosts += group_hosts['hosts']
                extra_vars = group_hosts.get('vars')

        if options.disable_pubkey and options.password is None:
            raise ArgumentError(
                '--disable-pubkey required but no --password provided.')

        if options.task_name is None:
            raise ArgumentError(
                'Specify a task to run, please. '
                'You can use -l to list tasks.')

        task = g.tasks.get(options.task_name)
        if task is None:
            print('\n\tunknown task: %s\n' % options.task_name)
            return

        kwargs = {}

        if options.args:
            for i in options.args:
                k, v = i.split(':', 1)
                kwargs[k] = v

        if options.quiet:
            env.keep_quiet = True

        # TODO project level logger
        print('Ploceusfile: %s' % ploceus_filename)
        print('task_name: %s' % options.task_name)
        print('host: %s' % hosts)
        print('keep_quiet: %s' % options.quiet)

        run_task(
            task, hosts,
            sleep=options.sleep,
            parallel=options.parallel,
            ssh_pwd=options.password,
            extra_vars=extra_vars,
            **kwargs
        )


    def list_tasks(self):
        if len(g.tasks) == 0:
            print('\n  No tasks defined.\n\n')
            return True

        print('\n  Available tasks:\n')
        for name in sorted(g.tasks.keys()):
            print('\t%s' % name)

        print('\n')


    def list_inventory(self):
        g.inventory.list_inventory()

def main():
    ploceus = Ploceus()
    ploceus.run()

if __name__ == '__main__':
    sys.exit(main())
