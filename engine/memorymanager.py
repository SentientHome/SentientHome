#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig

import logging as log
import asyncio
from aiohttp import web
import json
import time
from collections import defaultdict, deque

class shMemoryManager:
    'SentientHome event engine memory manager'

    def __init__(self, config, app):
        self._config = config
        self._app = app
        self._eventmemory = defaultdict(deque)

    @property
    def eventmemory(self):
        return self._eventmemory


#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
