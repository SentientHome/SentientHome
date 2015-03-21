#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.sheventhandler import shEventHandler
from common.shregistry import shRegistry

import logging as log
import requests
import json

config = shConfig('~/.config/home/home.cfg', name='Ubiquiti Unifi mFi Data')

# default to 5 sec polls - the frequency most sensors report back to the controller
handler = shEventHandler(config,\
                         config.getfloat('ubnt_mfi', 'ubnt_mfi_poll_interval', 5),\
                         dedupe=True)

retries = 0

# Setup session and login
session = requests.session()
r = session.post('https://' + config.get('ubnt_mfi', 'ubnt_mfi_addr') +\
                  '/login',\
                  {'username': config.get('ubnt_mfi', 'ubnt_mfi_user'),\
                   'password': config.get('ubnt_mfi', 'ubnt_mfi_pass'),\
                   'login':'Login'},\
                  verify=config.getboolean('ubnt_mfi', 'ubnt_mfi_verify_ssl'))

while True:
    # Get all sensors and their most current data
    # We can do this 10x per second if needed to drive down latency
    # This is just the polling part, we then auto dedupe the data to only
    # emit changed sensor values to the engine and event store
    r = session.get('https://' + config.get('ubnt_mfi', 'ubnt_mfi_addr') +\
                    '/api/v1.0/list/sensors',\
                    verify=config.getboolean('ubnt_mfi', 'ubnt_mfi_verify_ssl'))

    data = json.loads(r.text)

    for sensor in data['data']:
        event = [{
            'name': shRegistry['ubnt.mfi']['name'] + '.sensor', # Time Series Name
            'columns': list(sensor.keys()), # Keys
            'points': [list(sensor.values())] # Data points
        }]

        log.debug('Event: %s', event)
        # dedupe automatically ignores events we have processed before
        # This is where the dedupe magic happens. The event handler has deduping
        # built in and keeps an in-memory cache of events of the past 24h for that
        # In this case only changed sensor data points will get emitted and stored
        handler.postEvent(event, dedupe=True)

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('ubnt_mfi', 'ubnt_mfi_poll_interval', 5))
