# -*- coding: utf-8 -*-
import sys

from ploceus import g
from ploceus import ploceusfile
from ploceus.exceptions import ArgumentError
from ploceus.inventory import Inventory
from ploceus.task import TaskRunner



def usage():
    print('\n  Ploceus, programmer-friendly automated remote execution tool.')
    print('')
    print('    ploceus [options] <task_name>\n')
    print('\t-h, --help            show this help')
    print('\t-l, --list-tasks      list all avaiable tasks')
    print('\t-f, --ploceus-file    specify Ploceusfile')
    print('\t-H, --hosts           specify hosts')
    print('\t-i, --inventory       specify inventory file / directory')
    print('\t-g, --group           specify group of hosts in inventory')
    print('\t-P, --parallel        run task across hosts parallelly')
    print('\t--list-inventory      list all avaiable groups of hosts')
    print('\n')


class Ploceus(object):


    def __init__(self):
        self.ploceusfile = None
        self.should_list_tasks = False
        self.should_list_inventory = False
        self.hosts = []
        self.task_name = None
        self.group = None
        self.parallel = False


    def run(self):
        if len(sys.argv) == 1:
            usage()
            return

        exit = self._handle_args(sys.argv[1:])

        if self.ploceusfile is None:
            ploceusfile.find_ploceusfile()
        else:
            ploceusfile.ploceusfile_from_pyfile(self.ploceusfile)

        if exit:
            return 0

        if self.should_list_tasks:
            self.list_tasks()
            return 0

        if self.should_list_inventory:
            if g.inventory.empty:
                raise ArgumentError('cannot find inventory.')
            self.list_inventory()
            return 0

        if self.group and g.inventory.empty:
            raise ArgumentError('Specify inventory when using group, please.')

        extra_vars = None
        if self.group:
            group_hosts = g.inventory.get_target_hosts(self.group)
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

        task = g.tasks.get(self.task_name)
        if task is None:
            print('\n\tunknown task: %s\n' % self.task_name)
            return

        TaskRunner.run_task_with_hosts(task, self.hosts, self.parallel)


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


    def set_ploceusfile(self, args):
        args.pop(0)
        self.ploceusfile = args.pop(0)


    def set_hosts(self, args):
        args.pop(0)

        while len(args) > 1 and not args[0].startswith('-'):
            self.hosts.append(args.pop(0).strip())


    def set_inventory(self, args):
        args.pop(0)

        g.inventory = inventory = Inventory(args.pop(0))


    def set_group(self, args):
        args.pop(0)

        self.group = args.pop(0)


    def set_parallel(self, args):
        args.pop(0)

        self.parallel = True


    def _handle_args(self, args):
        exit = False

        if len(args) == 0:
            usage()
            return True

        while len(args) > 0:
            if exit:
                return exit

            if args[0].strip() in ('-h', '--help'):
                usage()
                return True

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

            if args[0].strip() in ('-g', '--group'):
                self.set_group(args)
                continue

            if args[0].strip() in ('-P', '--parallel'):
                self.set_parallel(args)
                continue

            if args[0].strip() in ('--list-inventory'):
                args.pop(0)
                self.should_list_inventory = True
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
