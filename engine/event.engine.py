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

import logging as log
log.info('Starting Sentient Home Event Engine')

@asyncio.coroutine
def handle_info(request):
    output = {'msg' : 'SentientHome Event Engine'}
    return web.Response(body=json.dumps(output).encode('utf-8'))

@asyncio.coroutine
def handle_event(request):

    text = yield from request.text()
    data = json.loads(text)
    log.debug('Event Type: %s', data[0]['name'], )

    output = {'msg' : 'Event Received'}
    return web.Response(body=json.dumps(output).encode('utf-8'))

@asyncio.coroutine
def init(loop):
    eaddr = config.get('sentienthome', 'event_addr')
    eport = config.get('sentienthome', 'event_port')
    epath = config.get('sentienthome', 'event_path')

    app = web.Application(loop=loop, logger=None)
    app.router.add_route('GET', '/', handle_info)
    app.router.add_route('GET', '/info', handle_info)
    app.router.add_route('POST', epath, handle_event)

    handler = app.make_handler()

    srv = yield from loop.create_server(handler, eaddr, eport)
    log.info("Event Engine started at http://%s:%s", eaddr, eport)
    return app, srv, handler

@asyncio.coroutine
def finish(app, srv, handler):
    log.info('Shuting down Event Engine...')
    yield from asyncio.sleep(0.1)
    srv.close()
    yield from handler.finish_connections()
    yield from srv.wait_closed()
    log.info('Good Bye!')


loop = asyncio.get_event_loop()
app, srv, handler = loop.run_until_complete(init(loop))

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(finish(app, srv, handler))
