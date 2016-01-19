# -*- coding: utf-8 -*-
import sys

from .commander import Commander



cmdr = Commander()

def main():
    cmdr.run()

if __name__ == '__main__':
    sys.exit(main())
