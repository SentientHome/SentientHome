#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
config = shConfig('~/.config/home/home.cfg')

import asyncio
from aiohttp import web
import json
import time
from collections import defaultdict, deque

# Restful/JSON interface API for event engine
from restinterface import shRestInterface
# In memory data manager for processing and persitance
from memorymanager import shMemoryManager

import logging as log
log.info('Starting Sentient Home Event Engine')

@asyncio.coroutine
def handle_event(request):

    try:
        text = yield from request.text()
        event = json.loads(text)

        # Assemble individual events from incoming stream
        #
        for e in event:
            log.debug('Event Type: %s', e['name'], )
            # Initialize event cache if it does not exist yet
            if not memory.eventmemory[e['name']]:
                # TODO: Lookup cache size from config
                memory.eventmemory[e['name']] = deque(maxlen=5000)

            for p in e['points']:
                if len(e['columns']) != len(p):
                    log.error('Number of Columns %s mismatches number of Points %s',\
                                len(e['columns']), len(p))
                myevent = dict()

                # Carry forward initial timestamp from feed
                myevent['shtime1'] = e['shtime1']
                # Timestamp the assembled event in milliseconds since epoch
                myevent['shtime2'] = time.time()*1000
                for x in range(0, len(e['columns'])):
                    myevent[e['columns'][x]]=p[x]

                log.debug('myevent: %s', myevent)

                memory.eventmemory[e['name']].appendleft(myevent)

                log.info('Event Latency: %2.4sms',\
                    myevent['shtime2']-myevent['shtime1'])

        output = {'msg' : 'Event Received'}
    except Exception as e:
        log.Error('Event Error: %s', e)
        output = {'msg' : 'Event Error; Event Rejected'}

    return web.Response(body=json.dumps(output).encode('utf-8'))

@asyncio.coroutine
def init(loop):
    eaddr = config.get('sentienthome', 'event_addr')
    eport = config.get('sentienthome', 'event_port')
    epath = config.get('sentienthome', 'event_path')

    app = web.Application(loop=loop, logger=None)

    # Handle incoming events
    app.router.add_route('POST', epath, handle_event)

    memory = shMemoryManager(config, app)

    # Register and implement all other RESTful interfaces
    interface = shRestInterface(config, app, memory);

    handler = app.make_handler()

    srv = yield from loop.create_server(handler, eaddr, eport)
    log.info("Event Engine started at http://%s:%s", eaddr, eport)
    return app, srv, handler, memory, interface

@asyncio.coroutine
def finish(app, srv, handler, memory):
    log.info('Shuting down Event Engine...')
    yield from asyncio.sleep(0.1)
    srv.close()
    yield from handler.finish_connections()
    yield from srv.wait_closed()
    log.info('Good Bye!')


loop = asyncio.get_event_loop()
app, srv, handler, memory, interface = loop.run_until_complete(init(loop))

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(finish(app, srv, handler, memory))
