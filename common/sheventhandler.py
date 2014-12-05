#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import logging as log
import requests
import json
import time

class shEventHandler:
    'SentientHome event handler'

    def __init__(self, config, poll_intervall=10):
        self._config = config
        self._poll_intervall = poll_intervall

        self.checkPoint()

    def postEvent(self, event):
        # First deposit the event data into our event store
        if self._config.event_store_active == 1:
            try:
                r = requests.post(self._config.event_store_path, data=json.dumps(event))
                log.info('Event store response: %s', r)
            except Exception:
                # Report a problem but keep going...
                log.warn('Exception posting data to event store: %s',\
                                self._config.event_store_path_safe)
                pass

        # Now post the same event into our event engine if active
        if self._config.event_engine_active == 1:
            try:
                r = requests.post(self._config.event_engine_path, data=json.dumps(event))
                log.info('Event engine response: %s', r)
            except Exception:
                # Report a problem but keep going...
                log.warn('Exception posting data to event engine: %s',\
                                self._config.event_engine_path_safe)
                pass

    def checkPoint(self):
        self._checkpoint = time.clock()

    def sleep(self):
        # Put processing to sleep until next polling interval

        if self._poll_intervall >= 0:
            # Logic to true up the poll intervall time for time lost processing
            time_to_sleep = self._poll_intervall -\
                            (time.clock() -\
                            self._checkpoint)
            # Enforce minimum of .1 sec and avoid negative
            if time_to_sleep < .1: time_to_sleep = .1

            log.debug('Time to sleep: %fs', time_to_sleep)
            time.sleep(time_to_sleep)
        else:
            log.warn('No poll intervall defined. Nothing to sleep.')

        self.checkPoint()

        # Leverage end of donwtime to check for updated config file
        self._config.reloadModifiedConfig()


    @property
    def config(self):
        return self._config

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
