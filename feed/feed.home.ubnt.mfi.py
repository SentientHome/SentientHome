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
handler = shEventHandler(config, config.getfloat('ubnt_mfi', 'ubnt_mfi_poll_interval', 5), dedupe=True)

retries = 0

# Setup session and login
session = requests.session()
addr = config.get('ubnt_mfi', 'ubnt_mfi_addr')
r = session.post('https://' + addr + '/login',\
                    {'username': config.get('ubnt_mfi', 'ubnt_mfi_user'),\
                     'password': config.get('ubnt_mfi', 'ubnt_mfi_pass'),\
                     'login':'Login'},\
                      verify=config.getboolean('ubnt_mfi', 'ubnt_mfi_verify_ssl'))

while True:
    # Get all earthquakes of the past hour
    r = session.get('https://' + addr + '/api/v1.0/list/sensors',\
                    verify=config.getboolean('ubnt_mfi', 'ubnt_mfi_verify_ssl'))

    data = json.loads(r.text)

    log.debug('Data: %s', data)

    for sensor in data['data']:
        event = [{
            'name': shRegistry['ubnt.mfi']['name'] + '.sensor', # Time Series Name
            'columns': list(sensor.keys()), # Keys
            'points': [list(sensor.values())] # Data points
        }]

        log.debug('Event: %s', event)
        # dedupe automatically ignores events we have processed before
        handler.postEvent(event, dedupe=True)

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('ubnt_mfi', 'ubnt_mfi_poll_interval', 5))

    # Reset poll path before looping with latest setting
    addr = config.get('ubnt_mfi', 'ubnt_mfi_addr')
