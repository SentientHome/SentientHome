#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.abspath('..'))

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import numerify
from common.sheventhandler import shEventHandler
from dependencies.ISY.IsyEvent import ISYEvent

import logging as log
log.info('Starting feed for Universal Devices ISY994')

import requests
import time

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config)

last_time = time.time()

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

    if (time.time() - last_time) > 10:
        config.reloadModifiedConfig()

# Setup ISY socket listener
# Be aware: Even though we are able to update the config at runtime
# we do not take down the web socket subscription once established
server = ISYEvent()
server.subscribe(addr=config.get('isy', 'isy_addr'),\
                 userl=config.get('isy', 'isy_user'),\
                 userp=config.get('isy', 'isy_pass'))
server.set_process_func(eventFeed, "")

try:
    print "Use Control-C to exit"
    server.events_loop()   #no return
except KeyboardInterrupt:
    log.info('Exiting...')
