#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import time
import configparser
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
        try:
            self._checkpoint_filename = os.path.join(
                os.path.expanduser(self._app.config.get(
                    'SentientHome', 'data_path')),
                self._app.origin_filename + '.p')
        except configparser.Error as e:
            self._app.log.fatal('Missing configuration setting: %s' % e)
            self._app.close(1)

        # See if we can restore the event memory from a previsous checkpoint
        try:
            with open(self._checkpoint_filename, 'rb') as f:
                # The protocol version used is detected automatically
                self._eventmemory = pickle.load(f)
        except (OSError, EOFError, FileNotFoundError) as e:
            self._app.log.warn(e)
            self._app.log.warn('Unable to read checkpoint file: %s' %
                               self._checkpoint_filename)
            pass

    def checkpoint(self):
        # persist memory manager to disk
        self._app.log.debug('Checkpoint memory manager: %s' %
                            self._checkpoint_filename)

        # Measure time spent on checkpointing
        time1 = time.monotonic()*1000

        temp = self._eventmemory

        time2 = time.monotonic()*1000

        try:
            with open(self._checkpoint_filename, 'wb') as f:
                # Pickle the event memory using the highest protocol available.
                pickle.dump(temp, f, pickle.HIGHEST_PROTOCOL)
        except OSError:
            self._app.log.warning('Unable to write checkpoint file: %s' %
                                  self._checkpoint_filename)
            pass

        time3 = time.monotonic()*1000

        self._app.log.debug('Time to copy(): %4.2sms' % time2 - time1)
        self._app.log.debug('Time to pickle(): %4.2sms' % time3 - time2)
        self._app.log.debug('Total time to checkpoint(): %4.2sms' %
                            time3 - time1)

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
