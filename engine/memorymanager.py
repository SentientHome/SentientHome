#!/usr/local/bin/python3 -u
"""
    Author:     Oliver Ratzesberger <https://github.com/fxstein>
    Copyright:  Copyright (C) 2016 Oliver Ratzesberger
    License:    Apache License, Version 2.0
"""

# Make sure we have access to SentientHome commons
import os
import sys
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
except:
    exit(1)

import time
from collections import defaultdict, deque
import pickle


class shMemoryManager:
    'SentientHome event engine memory manager'

    def __init__(self, app, loop):
        self._app = app
        self._loop = loop
        self._eventmemory = defaultdict(defaultdict)
        self._eventmemory['raw'] = defaultdict(deque)
        self._eventmemory['state'] = defaultdict(defaultdict)
        # TODO: Look up length from config
        self._eventmemory['action'] = deque(maxlen=5000)

        # Assemble a filename for the physical checkpoint
        self._checkpoint_filename = os.path.join(
            os.path.expanduser(self._app.config.get(
                'SentientHome', 'data_path')),
            self._app.origin_filename + '.p')

        if app.checkpointing is True:
            # See if we can restore the event memory from a previsous checkpoint
            try:
                with open(self._checkpoint_filename, 'rb') as f:
                    app.log.debug('Restoring from previous checkpoint: %s' %
                                  self._checkpoint_filename)
                    # The protocol version used is detected automatically
                    self._eventmemory = pickle.load(f)
            except (OSError, EOFError, FileNotFoundError) as e:
                app.log.warn(e)
                app.log.warn('Unable to read checkpoint file: %s' %
                             self._checkpoint_filename)
                pass

    def checkpoint(self):
        if self._app.checkpointing is True:
            # persist memory manager to disk
            self._app.log.debug('Checkpoint memory manager: %s' %
                                self._checkpoint_filename)

            # Measure time spent on checkpointing
            time1 = time.monotonic()*1000

            temp = self._eventmemory

            time2 = time.monotonic()*1000

            try:
                with open(self._checkpoint_filename, 'wb') as f:
                    # Pickle the event memory
                    pickle.dump(temp, f, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                self._app.log.error('Unable to write checkpoint file: %s' %
                                    self._checkpoint_filename)
                self._app.log.error(e)
                pass

            time3 = time.monotonic()*1000

            self._app.log.debug('Time to copy(): %0.2fms' % (time2 - time1))
            self._app.log.debug('Time to pickle(): %0.2fms' % (time3 - time2))
            self._app.log.debug('Total time to checkpoint(): %0.2fms' %
                                (time3 - time1))

    @property
    def eventmemory(self):
        return self._eventmemory

    @property
    def action(self):
        return self._eventmemory['action']

    @property
    def raw(self):
        return self._eventmemory['raw']

    @property
    def state(self):
        return self._eventmemory['state']

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
