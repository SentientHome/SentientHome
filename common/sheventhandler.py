#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import logging as log
import requests
import json
import time
import os
import pickle

class shEventHandler:
    'SentientHome event handler'

    def __init__(self, config, poll_interval=10, dedupe=False):
        self._config = config

        log.info('Starting feed for %s', self._config.name)

        self._poll_interval = poll_interval
        # See if we need to enable deduping logic
        self._dedupe = dedupe
        # Empty event cache - Needed to dedup incoming events if we have processed them
        self._events = list()
        self._events_modified = False

        self.checkPoint()

        # If we are require to dedupe re-read the checkpoint file
        if self._dedupe==True:
            self._checkpoint_filename = os.path.join(\
                    self._config.get('sentienthome', 'checkpoint_path'),\
                    self._config.origin_filename + '.p')
            # See if we can restore the event cache from a previsous checkpoint
            try:
                with open(self._checkpoint_filename, 'rb') as f:
                    # The protocol version used is detected automatically, so we do not
                    # have to specify it.
                    self._events = pickle.load(f)
            except (OSError, EOFError) as e:
                log.warning('Unable to read checkpoint file: %s', self._checkpoint_filename)
                pass

    def postEvent(self, event, dedupe=False):
        if dedupe == True:
            if self._dedupe == True:
                if event in self._events:
                    log.debug('Supressing duplicate event: %s', event)
                    return
                else:
                    self._events_modified = True
                    self._events.insert(0, event)
            else:
                log.warning('Eventhandler dedupe logic not inititalized. Ignoring dedupe.')

        # First deposit the event data into our event store
        if self._config.event_store_active == 1:
            try:
                r = requests.post(self._config.event_store_path, data=json.dumps(event))
                if r.status_code == 200:
                    log.info('Event store response: %s', r)
                else:
                    log.warn('Event store response: %s', r)
                    log.warn('Event rejected by %s', self._config.event_store_path_safe)
                    log.warn('Event data: %s', event)
            except Exception:
                # Report a problem but keep going...
                log.error('Exception posting data to event store: %s',\
                                self._config.event_store_path_safe)
                pass

        # Now post the same event into our event engine if active
        if self._config.event_engine_active == 1:
            try:
                r = requests.post(self._config.event_engine_path, data=json.dumps(event))
                if r.status_code == 200:
                    log.info('Event engine response: %s', r)
                else:
                    log.warn('Event engine response: %s', r)
                    log.warn('Event rejected by %s', self._config.event_engine_path_safe)
                    log.warn('Event data: %s', event)
            except Exception:
                # Report a problem but keep going...
                log.error('Exception posting data to event engine: %s',\
                                self._config.event_engine_path_safe)
                pass

    def checkPoint(self, write=False):
        if self._dedupe == True and write == True and self._events_modified == True:
            # Before taking  checkpoint lets prune the cache and remove old events
            # We keep 2 time the daily interval rate
            maxlength = (int)(2 * 86400 / self._poll_interval)
            del self._events[maxlength:]

            try:
                with open(self._checkpoint_filename, 'wb') as f:
                    # Pickle the 'data' dictionary using the highest protocol available.
                    pickle.dump(self._events, f, pickle.HIGHEST_PROTOCOL)
            except OSError:
                log.warning('Unable to write checkpoint file: %s', self._checkpoint_filename)
                pass

            # Now that we have written the checkpoint file reset modified flag
            self._events_modified = False


        self._checkpoint = time.clock()

    def sleep(self, poll_interval=''):
        # Update poll_interval if supplied
        if poll_interval != '': self._poll_interval = poll_interval

        # Put processing to sleep until next polling interval

        if self._poll_interval >= 0:
            # Logic to true up the poll intervall time for time lost processing
            time_to_sleep = self._poll_interval -\
                            (time.clock() -\
                            self._checkpoint)
            # Enforce minimum of .1 sec and avoid negative
            if time_to_sleep < .1: time_to_sleep = .1

            log.debug('Time to sleep: %fs', time_to_sleep)
            time.sleep(time_to_sleep)
        else:
            log.warn('No poll intervall defined. Nothing to sleep.')

        if self._dedupe == True:
            log.debug('Event Cache Count: %s', len(self._events))

        self.checkPoint(write=True)

        # Leverage end of donwtime to check for updated config file
        self._config.reloadModifiedConfig()

    # RESTful helper to handle retries
    def get(self, url, auth=None):
        retries = 0

        while True:
            try:
                return requests.get(url, auth=auth)
            except Exception:
                retries += 1

                log.warn('Cannot GET from %s. Attempt %n of %n',\
                         self._config.name, retries, self._config.retries)

                if retries >= self._config.retries:
                    log.Error('Cannot GET from to %s. Exiting...',\
                              self._config.name)
                    raise

                # Wait for the next poll intervall until we retry
                # also allows for configuration to get updated
                self.sleep()
                continue

    # RESTful helper to handle retries
    def post(self, url, auth=None, data=None):
        retries = 0

        while True:
            try:
                return requests.post(url, auth=auth, data=data)
            except Exception:
                retries += 1

                log.warn('Cannot POST to %s. Attempt %n of %n',\
                         self._config.name, retries, self._config.retries)

                if retries >= self._config.retries:
                    log.Error('Cannot POST to %s. Exiting...',\
                              self._config.name)
                    raise

                # Wait for the next poll intervall until we retry
                # also allows for configuration to get updated
                self.sleep()
                continue

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
