#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import xml_to_dict
from common.sheventhandler import shEventHandler

import logging as log
log.info('Starting feed for Autelis PentAir Easytouch Controller')

import requests

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config, config.getfloat('autelis', 'autelis_poll_interval', 10))

retries = 0

while True:
    try:
        r = requests.get('http://' + config.get('autelis', 'autelis_addr') +\
                         '/status.xml', auth=(config.get('autelis', 'autelis_user'),\
                         config.get('autelis', 'autelis_pass')))
        # Data Structure Documentation: http://www.autelis.com/wiki/index.php?
        # title=Pool_Control_(PI)_HTTP_Command_Reference
    except Exception:
        retries += 1

        log.warn('Cannot connect to Autelis. Attempt %n of %n',\
                        retries, config.retries)

        if retries >= config.retries:
            log.Error('Cannot connect to Autelis. Exiting...')
            raise

        # Wait for the next poll intervall until we retry
        # also allows for configuration to get updated
        handler.sleep(config.getfloat('autelis', 'autelis_poll_interval', 10))
        continue

    # Reset retries once we get a valid response
    retries = 0

    log.debug('Fetch data: %s', r.text)

    data = xml_to_dict(r.text)

    alldata = dict(list(data['response']['equipment'].items()) + \
                    list(data['response']['system'].items()) + \
                    list(data['response']['temp'].items()))

    event = [{
        'name': 'pool', # Time Series Name
        'columns': list(alldata.keys()), # Keys
        'points': [ list(alldata.values()) ] # Data points
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('autelis', 'autelis_poll_interval', 10))
