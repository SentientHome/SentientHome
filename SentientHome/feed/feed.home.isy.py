#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import numerify
from common.sheventhandler import shEventHandler
from dependencies.ISY.IsyEvent import ISYEvent

import logging as log
log.info('Starting feed for Universal Devices ISY994')

import requests

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config)

# Realtime event feeder
def eventFeed(*arg):

    data = arg[0]

    event = [{
        'name': 'isy',
        'columns': data.keys(),
        'points': [ data.values() ]
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    # Reload config if modified - self limited to once every 10s+
    config.reloadModifiedConfig()

# Setup ISY socket listener
# Be aware: Even though we are able to update the config at runtime
# we do not take down the web socket subscription once established
server = ISYEvent()

retries = 0

while True:
    try:
        server.subscribe(addr=config.get('isy', 'isy_addr'),\
                         userl=config.get('isy', 'isy_user'),\
                         userp=config.get('isy', 'isy_pass'))
        break
    except Exception:
        retries += 1

        log.warn('Cannot connect to ISY. Attempt %n of %n',\
                        retries, config.retries)

        if retries >= config.retries:
            log.Error('Unable to connect to ISY. Exiting...')
            raise

        # Wait for the next poll intervall until we retry
        # also allows for configuration to get updated
        handler.sleep()
        continue


server.set_process_func(eventFeed, "")

try:
    print "Use Control-C to exit"
    server.events_loop()   #no return
except KeyboardInterrupt:
    log.info('Exiting...')
