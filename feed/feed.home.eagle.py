#!/usr/local/bin/python3 -u
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

import logging as log

import json

config = shConfig('~/.config/home/home.cfg', name='Rainforest Eagle Gateway')
handler = shEventHandler(config,\
                         config.getfloat('raineagle', 'eagle_poll_interval', 5))

command =  '<LocalCommand>\n\
                <Name>get_device_list</Name>\n\
            </LocalCommand>'

r = handler.post('http://' + config.get('raineagle', 'eagle_addr') +\
                 '/cgi-bin/cgi_manager', data=command)
log.debug('Fetch data: %s', r.text)

device = json.loads(r.text)
device_macid = device['device_mac_id[0]']

command =  '<LocalCommand>\n\
                <Name>get_usage_data</Name>\n\
                <MacId>' + device_macid + '</MacId>\n\
            </LocalCommand>'

while True:
    r = handler.post('http://' + config.get('raineagle', 'eagle_addr') +\
                     '/cgi-bin/cgi_manager', data=command)
    log.debug('Fetch data: %s', r.text)

    devicedata = dict((k, numerify(v)) for k, v in json.loads(r.text).items())

    if devicedata['demand_units'] == 'W':
        power = devicedata['demand']
    elif devicedata['demand_units'] == 'kW':
        power = devicedata['demand'] * 1000
    else:
        log.error( 'Unsupport demand units: %s', devicedata['demand_units'] )

    if devicedata['summation_units'] == 'Wh':
        received  = devicedata['summation_received']
        delivered = devicedata['summation_delivered']
    elif devicedata['summation_units'] == 'kWh':
        received  = devicedata['summation_received'] * 1000
        delivered = devicedata['summation_delivered'] * 1000
    elif devicedata['summation_units'] == 'MWh':
        received  = devicedata['summation_received'] * 1000 * 1000
        delivered = devicedata['summation_delivered'] * 1000 * 1000
    else:
        log.error( 'Unsupport summation units: %s', devicedata['summation_units'] )

    amps = power/240

    event = [{
        'name': 'power',
        'columns': [ 'whole_house_power', 'whole_house_amps', 'whole_house_received', 'whole_house_delivered' ],
        'points': [[ power, amps, received, delivered ]]
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('raineagle', 'eagle_poll_interval', 5))
