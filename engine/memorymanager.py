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
import pickle
from copy import deepcopy


class shMemoryManager:
    'SentientHome event engine memory manager'

    def __init__(self, config, app, loop):
        self._config = config
        self._app = app
        self._loop = loop
        self._eventmemory = defaultdict(deque)

        # Assemble a filename for the physical checkpoint
        self._checkpoint_filename = os.path.join(\
                os.path.expanduser(self._config.get('sentienthome', 'data_path')),\
                self._config.origin_filename + '.p')

        # See if we can restore the event memory from a previsous checkpoint
        try:
            with open(self._checkpoint_filename, 'rb') as f:
                # The protocol version used is detected automatically, so we do not
                # have to specify it.
                self._eventmemory = pickle.load(f)
        except (OSError, EOFError) as e:
            log.warning('Unable to read checkpoint file: %s', self._checkpoint_filename)
            pass

    def checkpoint(self):
        # persist memory manager to disk
        log.debug('Checkpoint memory manager: %s', self._checkpoint_filename)

        # Measure time spent on checkpointing
        time1 = time.monotonic()*1000

        # Need a true copy of the in-memory structure for asyncronous IO to disk
        temp = deepcopy(self._eventmemory)

        time2 = time.monotonic()*1000

        try:
            with open(self._checkpoint_filename, 'wb') as f:
                # Pickle the event memory using the highest protocol available.
                pickle.dump(temp, f, pickle.HIGHEST_PROTOCOL)
        except OSError:
            log.warning('Unable to write checkpoint file: %s', self._checkpoint_filename)
            pass

        time3 = time.monotonic()*1000

        log.debug('Time to deepcopy(): %4.2sms', (time2 - time1))
        log.debug('Time to pickle(): %4.2sms', time3 - time2)
        log.debug('Total time to checkpoint(): %4.2sms', time3 - time1)

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
