#!/usr/bin/env python

import ast
import re

from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('click_threading/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='click-threading',
    version=version,
    description='Multithreaded Click apps made easy',
    author='Markus Unterwaditzer',
    author_email='markus@unterwaditzer.net',
    url='https://github.com/click-contrib/click-threading',
    license='MIT',
    packages=['click_threading'],
    install_requires=[
        'click>=5.0',
    ],
    extras_require={
        ':python_version < "3.2"': 'futures'
    }
)
