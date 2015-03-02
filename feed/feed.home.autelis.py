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
from common.shregistry import shRegistry

import logging as log

config = shConfig('~/.config/home/home.cfg',\
                    name='Autelis PentAir Easytouch Controller')
handler = shEventHandler(config,\
                         config.getfloat('autelis', 'autelis_poll_interval', 10))

while True:
    try:
        r = handler.get('http://' + config.get('autelis', 'autelis_addr') +\
                             '/status.xml', auth=(config.get('autelis', 'autelis_user'),\
                             config.get('autelis', 'autelis_pass')))
            # Data Structure Documentation: http://www.autelis.com/wiki/index.php?
            # title=Pool_Control_(PI)_HTTP_Command_Reference

        log.debug('Fetch data: %s', r.text)

        data = xml_to_dict(r.text)

        alldata = dict(list(data['response']['equipment'].items()) + \
                       list(data['response']['system'].items()) + \
                       list(data['response']['temp'].items()))

        event = [{
            'name':    shRegistry['autelis']['name'], # Time Series Name
            'columns': list(alldata.keys()), # Keys
            'points':  [ list(alldata.values()) ] # Data points
        }]

        log.debug('Event data: %s', event)

        handler.postEvent(event)
    except Exception as e:
        log.error('Error: %s', e)
        pass

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('autelis', 'autelis_poll_interval', 10))
