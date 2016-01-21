# -*- coding: utf-8 -*-
import yaml
import os

from ploceus.exceptions import NoGroupFoundError




class Inventory(object):

    def __init__(self, inventory=None):
        self.inventory = inventory
        self._groups = None


    def _load_inventory(self):
        self._groups = dict()

        inventory = self.inventory

        if os.path.isfile(inventory):
            file_names = [inventory]
        elif os.path.isdir(inventory):
            file_names = filter(
                lambda x: os.path.isfile,
                map(lambda x: os.path.join(inventory, x),
                    os.listdir(inventory)))
        else:
            raise ValueError('not a valid invetory file: %s' % invetory)

        for fname in file_names:
            self._groups.update(self._parse_inventory(fname))


    def _parse_inventory(self, fname):
        with open(fname) as f:
            return yaml.load(f.read())


    @property
    def empty(self):
        if self._groups is None:
            return True
        return len(self._groups.keys()) <= 0


    def list_inventory(self):
        if self._groups is None:
            self._load_inventory()

        if len(self._groups.keys()) == 0:
            print('\n    No group defined.\n')

        print('\n  Available groups:\n')
        for name in sorted(self._groups.keys()):
            print('\t%s' % name)

        print('\n')


    def get_target_hosts(self, group_name):
        if self.empty:
            self._load_inventory()
        if self.empty:
            self.find_inventory()

        group = self._groups.get(group_name)
        if group is None:
            raise NoGroupFoundError('no group named %s found' % group_name)

        return group


    def find_inventory(self):
        if os.path.exists('hosts'):
            self.inventory = 'hosts'
            self._load_inventory()
