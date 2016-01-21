# -*- coding: utf-8 -*-
import yaml
import os

from ploceus.exceptions import NoGroupFoundError


def find_inventory():
    if os.path.exists('hosts'):
        return Inventory('hosts')


class Inventory(object):

    def __init__(self, inventory):
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


    def get_target_hosts(self, group_name):
        if self._groups is None:
            self._load_inventory()

        group = self._groups.get(group_name)
        if group is None:
            raise NoGroupFoundError('no group named %s found' % group_name)

        return group
