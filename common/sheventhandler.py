#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

import requests
import json
import time
import os
from collections import deque
import pickle
import copy


class shEventHandler:
    'SentientHome event handler'

    def __init__(self, app, interval_key='poll_interval', dedupe=False):
        self._app = app

        self._app.log.info('Starting feed for %s' % self._app._meta.label)

        self._interval_key = interval_key
        self._poll_interval = (float)(self._app.config.get(
            self._app._meta.label,
            self._interval_key,
            fallback=10.0))
        # See if we need to enable deduping logic
        self._dedupe = dedupe

        self.checkPoint()

        # If we are require to dedupe re-read the checkpoint file
        if self._dedupe is True:
            # Create empty event cache - Needed to dedup incoming events

            self._events_maxlen = (int)(self._app.config.get(
                self._app._meta.label,
                'events_max_len',
                fallback=-1))

            if self._events_maxlen == -1:
                self._events_maxlen = (int)(self._app.config.get(
                    'SentientHome',
                    'events_max_len',
                    fallback=10000))

                events_per_day = (int)(86400 / self._poll_interval)
                if events_per_day < self._events_maxlen:
                    self._events_maxlen = events_per_day

            self._app.log.debug('Maximum Dedupe Buffer Length: %s' %
                                self._events_maxlen)

            self._events = deque(maxlen=self._events_maxlen)
            self._events_modified = False
            # Assemble a filename for the physical checkpoint
            self._checkpoint_filename = os.path.join(
                os.path.expanduser(self._app.config.get('SentientHome',
                                                        'data_path')),
                self._app.origin_filename + '.p')
            # See if we can restore the event cache from a previsous checkpoint
            try:
                with open(self._checkpoint_filename, 'rb') as f:
                    # The protocol version used is detected automatically
                    self._events = pickle.load(f)
            except (OSError, EOFError) as e:
                self._app.log.warn(e)
                self._app.log.warn('Unable to read checkpoint file: %s' %
                                   self._checkpoint_filename)
                pass
            # Fianlly check if the current class version uses the same datatype
            if isinstance(deque(maxlen=self._events_maxlen),
                          type(self._events)) is False:
                # This is only a checkpoint: truncate, dont bother converting
                self._app.log.debug("Checkpoint file data type was: %s" %
                                    type(self._events))
                self._events = deque(maxlen=self._events_maxlen)
                self._app.log.debug("Checkpoint file data type now: %s" %
                                    type(self._events))

    def _postStore(self, event):
        if self._app.event_store_active == 1:
            try:
                r = self._app._event_store_client.write_points(event, 's')
                self._app.log.info('Event store response: %s' % r)
            except Exception as e:
                self._app.log.fatal(e)
                self._app.log.fatal('Exception posting data to event store: %s'
                                    % self._app._event_store_info)
                self._app.close(1)

    def _postEngine(self, event, timestamp):
        # Now post the same event into our event engine if active
        if self._app.event_engine_active == 1:
            event_for_engine = copy.deepcopy(event)
            # Apply the timestamp to all events heading to the event engine
            for e in event_for_engine:
                e['shtime1'] = timestamp

            try:
                r = self.post(self._app.event_engine_path,
                              data=json.dumps(event_for_engine))
                self._app.log.info('Event engine response: %s' % r)
            except Exception as e:
                self._app.log.fatal(e)
                self._app.log.fatal('Exception posting data to event engine: %s'
                                    % self._app.event_engine_path_safe)
                self._app.close(1)

    def _postListener(self, event, timestamp):
        # Now post the same event into the listener if active
        if self._app._listener_active == 1:
            event_for_listener = copy.deepcopy(event)
            # Apply the timestamp to all events heading to the event engine
            for e in event_for_listener:
                e['shtime1'] = timestamp

            try:
                r = self.post(self._app._listener_path,
                              data=json.dumps(event_for_listener),
                              headers=self._app._listener_auth)
                self._app.log.info('Listener response: %s' % r)
            except Exception as e:
                self._app.log.fatal(e)
                self._app.log.fatal('Exception posting data to listener: %s'
                                    % self._app._listener_path)
                self._app.close(1)

    def postEvent(self, event, dedupe=False):

        # Timestamp the event - only applied to events heading to event engine
        timestamp = time.time()

        # Engage deduping logic if required
        if dedupe is True and self._dedupe is True:
            if event in self._events:
                self._app.log.debug('Duplicate event: %.25s...' %
                                    event[0]['points'])

                # Nothing left to do here. The same event was already sent
                return
            else:
                self._events_modified = True
                self._events.appendleft(event)
        elif dedupe is True:
            self._app.log.warning('Eventhandler dedupe logic not \
                                   inititalized. Ignoring dedupe.')

        # First deposit the event data into our event store
        self._postStore(event)

        # Next send event data to our in-memory event engine
        self._postEngine(event, timestamp)

        # Next send event data to a generic Listener if configured
        self._postListener(event, timestamp)

    def checkPoint(self, write=False):
        if (self._dedupe and write and self._events_modified) is True:
            # Write checkpoint deque type manages maxlength automatically
            try:
                with open(self._checkpoint_filename, 'wb') as f:
                    # Pickle the event cache
                    pickle.dump(self._events, f, pickle.HIGHEST_PROTOCOL)
            except OSError:
                self._app.log.warning('Unable to write checkpoint file: %s' %
                                      self._checkpoint_filename)
                pass

            # Now that we have written the checkpoint file reset modified flag
            self._events_modified = False

        self._checkpoint = time.clock()

    def sleep(self, sleeptime=None):
        # Update poll_interval if supplied
        self._poll_interval = (float)(self._app.config.get(
            self._app._meta.label,
            self._interval_key,
            fallback=10.0))
        if sleeptime is None:
            stime = self._poll_interval
        else:
            stime = sleeptime

        if self._dedupe is True:
            self._app.log.debug('Event Cache Count: %s' % len(self._events))
            self._app.log.debug('Event Cache Max Size: %s' %
                                self._events.maxlen)

        prior_checkpoint = self._checkpoint
        self.checkPoint(write=True)

        # Put processing to sleep until next polling interval
        if stime >= 0:
            # Logic to true up the poll interval time for time lost processing
            time_to_sleep = stime - (time.clock() - prior_checkpoint)
            # Enforce minimum of .1 sec and avoid negative
            if time_to_sleep < .1:
                time_to_sleep = .1

            self._app.log.debug('Time to sleep: %fs' % time_to_sleep)
            time.sleep(time_to_sleep)
        else:
            self._app.log.warn('No poll interval or sleep time defined. \
                                Nothing to sleep.')

        self.checkPoint()

    # RESTful get helper to handle retries
    def get(self, url, auth=None):
        retries = 0

        while True:
            try:
                r = requests.get(url, auth=auth)
                if r.status_code not in [200, 201]:
                    self._app.log.error('Invalid status code: %s' %
                                        r.status_code)
                return r
            except Exception as e:
                retries += 1

                self._app.log.warn(e)
                self._app.log.warn('Cannot GET from %s. Attempt %s of %s' %
                                   (url, retries, self._app.retries))

                if retries >= self._app.retries:
                    self._app.log.error('Cannot GET from to %s. Exiting...' %
                                        url)
                    raise e

                # Wait until we retry
                self.sleep(self._app._retry_interval)
                continue

    # RESTful post helper to handle retries
    def post(self, url, auth=None, data=None, headers=None):
        retries = 0

        while True:
            try:
                r = requests.post(url, auth=auth, data=data, headers=headers)
                if r.status_code not in [200, 201]:
                    self._app.log.error('Invalid status code: %s' %
                                        r.status_code)
                return r
            except Exception as e:
                retries += 1

                self._app.log.warn(e)
                self._app.log.warn('Cannot POST to %s. Attempt %s of %s' %
                                   (url, retries, self._app.retries))

                if retries >= self._app.retries:
                    self._app.log.error('Cannot POST to %s. Exiting...' %
                                        url)
                    raise e

                # Wait until we retry
                self.sleep(self._app._retry_interval)
                continue

#
# Do nothing
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
