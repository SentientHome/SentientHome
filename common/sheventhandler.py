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

    def __init__(self, config, poll_intervall=-1.0):
        self._config = config
        self._poll_intervall = poll_intervall

        self.checkPoint()

    def postEvent(self, event):
        # First deposit the event data into our target store
        try:
            r = requests.post(self._config.target_path, data=json.dumps(event))
            log.info('Target store response: %s', r)
        except Exception:
            # Report a problem but keep going...
            log.warn('Exception posting data to %s', self._config.target_path_safe)
            pass

        # Now post the same event into our rules engine if active
        if self._config.rules_engine_active == 1:
            try:
                r = requests.post(self._config.rules_path, data=json.dumps(event))
                log.info('Rules engine response: %s', r)
            except Exception:
                # Report a problem but keep going...
                log.warn('Exception posting data to %s', self._config.rules_path_safe)
                pass

    def checkPoint(self):
        self._checkpoint = time.clock()

    def sleep(self):
        if self._poll_intervall >= 0:
            time_to_sleep = self._poll_intervall -\
                            (time.clock() -\
                            self._checkpoint)
            # Enforce minimum of .1 sec
            if time_to_sleep < .1: time_to_sleep = .1
            log.debug('Time to sleep: %fs', time_to_sleep)
            time.sleep(time_to_sleep)
        else:
            log.warn('No poll intervall defined. Nothing to sleep.')

        self.checkPoint()

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
