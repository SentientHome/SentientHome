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
from concurrent.futures import ThreadPoolExecutor

# Restful/JSON interface API for event engine
from restinterface import shRestInterface
# In memory data manager for processing and persitance
from memorymanager import shMemoryManager

# ISY helper
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/../dependencies/ISYlib-python')
from ISY.IsyClass import Isy


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

            # Initialize raw event cache if it does not exist yet
            if not memory.eventmemory['raw'][e['name']]:
                # TODO: Lookup cache size from config
                memory.eventmemory['raw'][e['name']] = deque(maxlen=5000)

            # Initialize state event cache if it does not exist yet
            if not memory.eventmemory['state'][e['name']]:
                memory.eventmemory['state'][e['name']] = defaultdict(deque)

            for p in e['points']:
                # Perform a simple sanity check
                if len(e['columns']) != len(p):
                    log.error('Number of Columns %s mismatches number of Points %s',\
                                len(e['columns']), len(p))

                # Populate raw event memory
                myevent = dict()

                # Carry forward initial timestamp from feed
                myevent['shtime1'] = e['shtime1']
                # Timestamp the assembled event in milliseconds since epoch
                myevent['shtime2'] = time.time()*1000
                for x in range(0, len(e['columns'])):
                    myevent[e['columns'][x]]=p[x]

                log.debug('myevent: %s', myevent)

                memory.eventmemory['raw'][e['name']].appendleft(myevent)

                # Populate state memory
                state = dict()
                state['time'] = e['shtime1']

                # Temporarily built isy status cache in here
                # TODO: Move into a plugin

                try:
                    if e['name'] == 'isy':
                        # Initialize state event cache if it does not exist yet
                        if not memory.eventmemory['state'][e['name']][myevent['Event.node']]:
                            memory.eventmemory['state'][e['name']][myevent['Event.node']] = deque(maxlen=100)

                        state['control'] = myevent['Event.control']
                        state['action'] = myevent['Event.action']

                        actions = ['DON', 'DFON', 'DOF', 'DFOF', 'ST', 'OL', \
                                   'RR', 'BMAN', 'SMAN', 'DIM', 'BRT']

                        if state['control'] in actions:
                            log.debug('==============================')
                            log.debug('Node: %s Data: %s', myevent['Event.node'], state)
                            log.debug('==============================')
                            memory.eventmemory['state'][e['name']][myevent['Event.node']].appendleft(state)
                except Exception as e:
                    log.Error('Error appending state: %s', e)

                # Fire event engine
                yield from fire(e['name'], myevent, state, memory)

                time3 = time.time()*1000

                # Report event latency
                log.info('Event Latency: %2.4sms',\
                    myevent['shtime2']-myevent['shtime1'])

                log.info('Event Processing Latency: %2.4sms',\
                    time3-myevent['shtime1'])


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

    memory = shMemoryManager(config, app, loop)

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

    # Perform final inline checkpoint as we are shutting down after this
    memory.checkpoint()
    log.info('Good Bye!')

@asyncio.coroutine
def checkpoint(loop, thread, memory):
    try:
        # TODO: Replace while loop with scheduled tasks...
        while(True):
            yield from loop.run_in_executor(thread, memory.checkpoint)
            # TODO: Need to make the checkpoints configurable
            yield from asyncio.sleep(120)
    except Exception:
        return

@asyncio.coroutine
def fire(etype, event, state, memory):
    try:
        log.debug('Firing event rules for: %s: %s, %s', etype, event, state)

        # TODO: The logic below is a temporary test and to be placed into
        # event engine plugins onve the kinks are worked out.

        if etype == 'isy' and  event['Event.node'] == '24 0 93 1':
            log.debug('!!!!!!!!!!FOUNTAIN!!!!!!!!!!!')
        elif etype == 'isy' and  event['Event.node'] == '29 14 86 1':
            log.debug('!!!!!!!!!!LIVING - WINDOW - OUTLET!!!!!!!!!!!')
        elif etype == 'isy' and state['control'] == 'DON':
            log.debug('Node: %s TURNED ON!!!!!!!!!!!!!!!!', node)
        elif etype == 'isy' and state['control'] == 'ST':
            log.debug('Node: %s SET TARGET!!!!!!!!!!!!!!!', node)
            
        # Test mFi Sensor rule
        if etype == 'ubnt.mfi.sensor' and event['label'] == 'Well.Well.Pump':
            if event['amps'] < 21 and event['amps'] > 15:
                # Turn off the well pump for set amount of time
                log.info('!!!!!!!! WELL PUMP SAVER ACTION !!!!!!!!!')

                myIsy = Isy(addr=config.get('isy', 'isy_addr'),\
                            userl=config.get('isy', 'isy_user'),\
                            userp=config.get('isy', 'isy_pass'))
                # First put pump to sleep
                well_pump = myIsy.get_node("Well - Well Pump")
                if well_pump:
                    well_pump.off()
                    # yield from asyncio.sleep(2)
                    # well_pump.off()
                    #
                    # # Then schedule wakeup at a later time
                    # yield from asyncio.sleep(900)
                    # well_pump.on()
                    # yield from asyncio.sleep(2)
                    # well_pump.on()


    except Exception:
        return


loop = asyncio.get_event_loop()
app, srv, handler, memory, interface = loop.run_until_complete(init(loop))

# Create a ThreadPool with 2 threads
thread = ThreadPoolExecutor(2)
# Create a task to perform ongoing checkpoints
loop.create_task(checkpoint(loop, thread, memory))

try:
    loop.run_forever()
except (KeyboardInterrupt, SystemExit):
    loop.run_until_complete(finish(app, srv, handler, memory))
