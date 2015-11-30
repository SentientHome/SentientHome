#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import asyncio
import json
import time
import copy

from aiohttp import web
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Sentient Home Application
from common.shapp import shApp
from cement.core.exc import CaughtSignal

# Restful/JSON interface API for event engine
from restinterface import shRestInterface
# In memory data manager for processing and persitance
from memorymanager import shMemoryManager

from cement.core import hook


class shEventEngine(shApp):
    class Meta:
        label = 'sheventengine'

        # Define hooks that plugins may implment to extend the event engine
        define_hooks = ['event_state',
                        'pre_process_event',
                        'process_event',
                        'post_process_event']

        plugin_dirs = ['~/SentientHome/plugins',
                       '~/SentientHome/rules']

        plugin_config_dirs = ['~/SentientHome/plugins',
                              '~/SentientHome/rules']

    def setup(self):
        # always run core setup first
        super(shEventEngine, self).setup()

        self.log.debug('setup()')

        self._loop = asyncio.get_event_loop()

        # Create a ThreadPool with 2 threads
        self._thread = ThreadPoolExecutor(2)

        hook.register('post_run', self._post_run, weight=-1)
        hook.register('pre_close', self._pre_close, weight=-1)

    def _post_run(self, app):
        self.log.debug('_post_run()')

        self._memory = shMemoryManager(self, self._loop)

        self._loop.run_until_complete(self.init(self._loop))

    def _pre_close(self, app):
        self.log.debug('_pre_close()')

        self._loop.run_until_complete(self.finish())

    def _checkpoint(self):

        app.log.debug('Checkpointing memory cache')

        try:
            self._loop.run_in_executor(self._thread, self._memory.checkpoint)
        except Exception as e:
            app.log.error('Unable to checkpoint memory cache')
            app.log.error(e)

        self._loop.call_later((int)(app.config.get('SentientHome',
                                                   'checkpoint_interval',
                                                   fallback=60)),
                              self._checkpoint)

    def run_forever(self):
        self._loop.run_forever()

    @asyncio.coroutine
    def init(self, loop):
        eaddr = self.config.get('SentientHome', 'event_addr')
        eport = self.config.get('SentientHome', 'event_port')
        epath = self.config.get('SentientHome', 'event_path')

        eaddr = eaddr.replace('http://', '')

        self._webapp = web.Application(loop=loop, logger=None)

        # Handle incoming events
        self._webapp.router.add_route('POST', epath, self.handle_event)

        # Register and implement all other RESTful interfaces
        # interface =
        shRestInterface(self)

        self._webapp_handler = self._webapp.make_handler()

        try:
            self._webapp_srv = yield from self._loop.create_server(
                self._webapp_handler, eaddr, eport)

            self.log.info("Event Engine started at http://%s:%s" %
                          (eaddr, eport))

            self._loop.call_later((int)(self.config.get('SentientHome',
                                                        'checkpoint_interval',
                                                        fallback=60)),
                                  app._checkpoint)
        except Exception as e:
            self.log.fatal("Unable to start RESTful interface at http://%s:%s" %
                           (eaddr, eport))
            self.log.fatal(e)
            self._loop.stop()

    @asyncio.coroutine
    def handle_event(self, request):
        self.log.debug('shEventEngine handle_event')

        try:
            text = yield from request.text()
            events = json.loads(text)

            # Assemble individual events from incoming stream
            #
            for event in events:
                self.log.debug('Event Type: %s' % event['measurement'])

                # Initialize raw event cache if it does not exist yet
                if not self._memory.raw[event['measurement']]:
                    # TODO: Lookup cache size from config
                    self._memory.raw[event['measurement']] = deque(maxlen=5000)

                # Populate raw event memory
                raw = copy.deepcopy(event)

                # Timestamp the assembled event
                raw['shtime2'] = time.time()

                # Remove redundant measurement name
                del raw['measurement']

                self.log.debug('raw event: %s' % raw)

                self._memory.raw[event['measurement']].appendleft(raw)

                # Enable plugins to define state/status caches specific to
                # one or more event types
                for res in hook.run('event_state', self,
                                    event['measurement'], raw):
                    pass

                # Enable pre event processing
                for res in hook.run('pre_process_event', self,
                                    event['measurement'], raw):
                    pass

                # Create a task to process event rule(s)
                # This allows us to quickly get back to the service call
                # while taking all the time we need to process the event
                # async
                self._loop.create_task(
                    self.process_event(event['measurement'], raw))

                time3 = time.time()

                # Report event latency
                self.log.info('Event Latency: %2.4sms' %
                              ((raw['shtime2'] - raw['shtime1'])*1000))

                self.log.info('Event Processing Init Latency: %2.4sms' %
                              ((time3 - raw['shtime1'])*1000))

            output = {'msg': 'Event Received'}
        except Exception as e:
            app.log.error('Event Error: %s' % e)
            output = {'msg': 'Event Error; Event Rejected'}

        return web.Response(body=json.dumps(output).encode('utf-8'))

    @asyncio.coroutine
    def process_event(self, event_type, event):
        self.log.debug('process_event() Event: %s %s' % (event_type, event))

        # Enable plugins to define state/status caches specific to
        # one or more event types
        for res in hook.run('process_event', self, event_type, event):
            pass

        # Enable post event processing
        for res in hook.run('post_process_event', self, event_type, event):
            pass

        time4 = time.time()

        # Report final event processing latency
        self.log.info('Event Processing Final Latency: %2.4sms' %
                      ((time4 - event['shtime1'])*1000))

    @asyncio.coroutine
    def finish(self):
        self.log.debug('shEventEngine finish')

        self.log.info('Shuting down Event Engine...')
        yield from asyncio.sleep(0.1)

        if hasattr(self, '_webapp_srv'):
            self._webapp_srv.close()
            yield from self._webapp_handler.finish_connections()
            yield from self._webapp_srv.wait_closed()

        # Perform final inline checkpoint as we are shutting down after this
        self._memory.checkpoint()
        self.log.info('Good Bye!')


with shEventEngine('shEventEngine') as app:
    app.run()
    app.log.info('Starting Sentient Home Event Engine')

    try:
        app.run_forever()
    except (KeyboardInterrupt, SystemExit, CaughtSignal):
        app.log.info('Shutting down Sentient Home Event Engine')

        app.close()
