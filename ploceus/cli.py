# -*- coding: utf-8 -*-
import sys

from ploceus import g
from ploceus import ploceusfile
from ploceus.exceptions import ArgumentError
from ploceus.inventory import Inventory, find_inventory



class Ploceus(object):


    def __init__(self):
        self.ploceusfile = None
        self.should_list_tasks = False
        self.hosts = []
        self.task_name = None
        self.inventory = None
        self.group = None


    def run(self):
        if len(sys.argv) == 1:
            # TODO: help usage
            return

        exit = self._handle_args(sys.argv[1:])
        if exit:
            return 0

        if self.ploceusfile is None:
            ploceusfile.find_ploceusfile()
        else:
            ploceusfile.ploceusfile_from_pyfile(self.ploceusfile)

        if self.inventory is None:
            self.inventory = find_inventory()

        if self.should_list_tasks:
            self.list_tasks()
            return 0

        if self.group and self.inventory is None:
            raise ArgumentError('Specify inventory when using group, please.')

        extra_vars = None
        if self.group:
            group_hosts = self.inventory.get_target_hosts(self.group)
            if group_hosts:
                self.hosts += group_hosts['hosts']
                extra_vars = group_hosts.get('vars')

        if self.task_name is None:
            raise ArgumentError(('Specify a task to run, please. '
                                 'You can use -l to list tasks.'))

        # TODO project level logger
        print('Ploceusfile: %s' % self.ploceusfile)
        print('task_name: %s' % self.task_name)
        print('hosts: %s' % self.hosts)

        # TODO: parallelism
        for host in self.hosts:
            task = g.tasks.get(self.task_name)
            if task is None:
                print('\n\tunknown task: %s\n' % self.task_name)
                return
            task.run(host, extra_vars)


    def list_tasks(self):
        if len(g.tasks) == 0:
            print('\n  No tasks defined.\n\n')
            return True

        print('\n  Available tasks:\n')
        for name in sorted(g.tasks.keys()):
            print('\t%s' % name)

        print('\n')


    def set_ploceusfile(self, args):
        args.pop(0)
        self.ploceusfile = args.pop(0)


    def set_hosts(self, args):
        args.pop(0)

        while len(args) > 1 and not args[0].startswith('-'):
            self.hosts.append(args.pop(0).strip())


    def set_inventory(self, args):
        args.pop(0)

        self.inventory = inventory = Inventory(args.pop(0))


    def set_group(self, args):
        args.pop(0)

        self.group = args.pop(0)


    def _handle_args(self, args):
        exit = False
        while len(args) > 0:
            if exit:
                return exit

            if args[0].strip() in ('-l', '--list-tasks'):
                args.pop(0)
                self.should_list_tasks = True
                continue

            if args[0].strip() in ('-f', '--ploceus-file'):
                self.set_ploceusfile(args)
                continue

            if args[0].strip() in ('-H', '--hosts'):
                self.set_hosts(args)
                continue

            if args[0].strip() in ('-i', '--inventory'):
                self.set_inventory(args)
                continue

            if args[0].strip() in ('-g', '--group'):
                self.set_group(args)
                continue

            self.task_name = args.pop(0)
            if len(args) > 1:
                print('\n\tplease specify all options before <task>\n')
                return True
            break

def main():
    ploceus = Ploceus()
    ploceus.run()

if __name__ == '__main__':
    sys.exit(main())
