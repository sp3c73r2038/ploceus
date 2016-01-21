# -*- coding: utf-8 -*-
import sys

from ploceus import ploceusfile
from ploceus import g



class Ploceus(object):


    def __init__(self):
        self.ploceusfile = None
        self.should_list_tasks = False
        self.hosts = []
        self.task_name = None


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

        if self.should_list_tasks:
            self.list_tasks()
            return 0

        print('Ploceusfile: %s' % self.ploceusfile)
        print('task_name: %s' % self.task_name)
        print('hosts: %s' % self.hosts)

        # TODO: parallelism
        for host in self.hosts:
            task = g.tasks.get(self.task_name)
            if task is None:
                print('\n\tunknown task: %s\n' % self.task_name)
                return
            task.run(host)


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


    def _handle_args(self, args):
        exit = False
        while len(args) > 0:
            if exit:
                return exit

            if args[0].strip() == '-l':
                args.pop(0)
                self.should_list_tasks = True
                continue

            if args[0].strip() == '-f':
                self.set_ploceusfile(args)
                continue

            if args[0].strip() == '-H':
                self.set_hosts(args)
                continue

            self.task_name = args.pop(0)
            if len(args) > 1:
                print('\n\tplease specify all options before <task>\n')
                return True
            break
