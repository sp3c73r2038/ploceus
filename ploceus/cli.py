# -*- coding: utf-8 -*-
import sys

from .commander import Commander
from .context import ContextManager


cmdr = Commander()
context_manager = ContextManager()


def main():
    cmdr.run()

if __name__ == '__main__':
    sys.exit(main())
