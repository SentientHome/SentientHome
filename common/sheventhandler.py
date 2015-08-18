#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import logging as log
import requests
import json
import time
import os
from collections import deque
import pickle
import copy

class shEventHandler:
    'SentientHome event handler'

    def __init__(self, app, interval_key, dedupe=False):
        self._app = app

        self._app.log.info('Starting feed for %s' % self._app._meta.label)

        self._interval_key = interval_key
        self._poll_interval = (int)(self._app.config.get(self._app._meta.label,
                                                         self._interval_key))
        # See if we need to enable deduping logic
        self._dedupe = dedupe

        self.checkPoint()

        # If we are require to dedupe re-read the checkpoint file
        if self._dedupe==True:
            # Empty event cache - Needed to dedup incoming events if we have processed them
            self._events_maxlen = (int)(86400 / self._poll_interval)
            self._events = deque(maxlen=self._events_maxlen)
            self._events_modified = False
            # Assemble a filename for the physical checkpoint
            self._checkpoint_filename = os.path.join(\
                    os.path.expanduser(self.app.config.get('sentienthome', 'data_path')),\
                    self._app.origin_filename + '.p')
            # See if we can restore the event cache from a previsous checkpoint
            try:
                with open(self._checkpoint_filename, 'rb') as f:
                    # The protocol version used is detected automatically, so we do not
                    # have to specify it.
                    self._events = pickle.load(f)
            except (OSError, EOFError) as e:
                self._app.log.warning('Unable to read checkpoint file: %s' %
                                        self._checkpoint_filename)
                pass
            # Fianlly check if the current class version uses the same datatype
            if type(self._events) != type(deque(maxlen=self._events_maxlen)):
                # This is only a checkpoint: truncate, dont bother converting
                self._app.log.debug("Checkpoint file data type was: %s" %
                                        type(self._events))
                self._events = deque(maxlen=self._events_maxlen)
                self._app.log.debug("Checkpoint file data type now: %s" %
                                        type(self._events))

    def postEvent(self, event, dedupe=False):

        # Timestamp the event - only apply to events heading to event engine
        timestamp = time.time()*1000

        # Engage deduping logic if required
        if dedupe == True:
            if self._dedupe == True:
                if event in self._events:
                    self._app.log.debug('Duplicate event: %.25s...' %
                                            event[0]['points'])

                    # Nothing left to do here. The very same event was already sent
                    return
                else:
                    self._events_modified = True
                    self._events.appendleft(event)
            else:
                self._app.log.warning('Eventhandler dedupe logic not inititalized. Ignoring dedupe.')

        # First deposit the event data into our event store
        if self._app.event_store_active == 1:
            try:
                r = self.post(self._app.event_store_path, data=json.dumps(event))
                self._app.log.info('Event store response: %s' % r)
            except Exception as e:
                self._app.log.fatal(e)
                self._app.log.fatal('Exception posting data to event store: %s' %
                                        self._app.event_store_path_safe)
                exit(1)

        # Need a true copy of the event or we would be messing with the cache
        event_for_engine = copy.deepcopy(event)
        # Apply the timestamp to all events heading to the event engine
        for e in event_for_engine:
            e['shtime1']=timestamp

        # Now post the same event into our event engine if active
        if self._app.event_engine_active == 1:
            try:
                r = self.post(self._app.event_engine_path,\
                            data=json.dumps(event_for_engine))
                self._app.log.info('Event engine response: %s' % r)
            except Exception as e:
                self._app.log.fatal(e)
                self._app.log.fatal('Exception posting data to event engine: %s' %
                                        self._app.event_engine_path_safe)
                exit(1)

    def checkPoint(self, write=False):
        if self._dedupe == True and write == True and self._events_modified == True:
            # Write checkpoint deque type manages maxlength automatically
            try:
                with open(self._checkpoint_filename, 'wb') as f:
                    # Pickle the 'data' dictionary using the highest protocol available.
                    pickle.dump(self._events, f, pickle.HIGHEST_PROTOCOL)
            except OSError:
                self._app.log.warning('Unable to write checkpoint file: %s' %
                                            self._checkpoint_filename)
                pass

            # Now that we have written the checkpoint file reset modified flag
            self._events_modified = False

        self._checkpoint = time.clock()

    def sleep(self, sleeptime = None):
        # Update poll_interval if supplied
        self._poll_interval = (int)(self._app.config.get(self._app._meta.label,
                                                         self._interval_key))
        if sleeptime == None:
            stime = self._poll_interval
        else:
            stime = sleeptime

        if self._dedupe == True:
            self._app.log.debug('Event Cache Count: %s' % len(self._events))
            self._app.log.debug('Event Cache Max Size: %s' % self._events.maxlen)

        prior_checkpoint = self._checkpoint
        self.checkPoint(write=True)

        # Put processing to sleep until next polling interval
        if stime >= 0:
            # Logic to true up the poll intervall time for time lost processing
            time_to_sleep = stime -\
                            (time.clock() -\
                            prior_checkpoint)
            # Enforce minimum of .1 sec and avoid negative
            if time_to_sleep < .1: time_to_sleep = .1

            self._app.log.debug('Time to sleep: %fs' % time_to_sleep)
            time.sleep(time_to_sleep)
        else:
            self._app.log.warn('No poll intervall or sleep time defined. Nothing to sleep.')

        self.checkPoint()

        # Leverage end of donwtime to check for updated config file
#        self._config.reloadModifiedConfig()

    # RESTful helper to handle retries
    def get(self, url, auth=None):
        retries = 0

        while True:
            try:
                r = requests.get(url, auth=auth)
                if r.status_code != 200:
                    raise ConnectionError('Invalid status code: %s' % r.status_code)
                return r
            except Exception as e:
                retries += 1

                self._app.log.warn(e)
                self._app.log.warn('Cannot GET from %s. Attempt %s of %s' %
                            (url, retries, self._app.retries))

                if retries >= self._app.retries:
                    self._app.log.error('Cannot GET from to %s. Exiting...' %
                              url)
                    raise

                # Wait until we retry
                self.sleep(self._app._retry_intervall)
                continue

    # RESTful helper to handle retries
    def post(self, url, auth=None, data=None, headers=None):
        retries = 0

        while True:
            try:
                r = requests.post(url, auth=auth, data=data, headers=headers)
                if r.status_code != 200:
                    raise ConnectionError('Invalid status code: %s' % r.status_code)
                return r
            except Exception as e:
                retries += 1

                self._app.log.warn(e)
                self._app.log.warn('Cannot POST to %s. Attempt %s of %s' %
                            (url, retries, self._app.retries))

                if retries >= self._app.retries:
                    self._app.log.error('Cannot POST to %s. Exiting...' %
                                            url)
                    raise

                # Wait until we retry
                self.sleep(self._app._retry_intervall)
                continue

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
