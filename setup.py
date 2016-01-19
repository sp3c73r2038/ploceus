# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='ploceus',
    packages=['ploceus'],
    version='0.0.1',
    install_requires=[
        'pycrypto==2.4.1',
        'paramiko'
    ],
    entry_points="""
    [console_scripts]
    ploceus=ploceus.cli:main
"""
)
