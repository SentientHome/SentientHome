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
log.info('Starting feed for Zillow home data')

import requests
import locale

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config, config.getfloat('zillow', 'zillow_poll_interval', 3600))

retries = 0

# set locale so we can easily strip the komma in the zindexValue
locale.setlocale( locale.LC_ALL, 'en_US' )

while True:
    try:
        r = requests.get('http://' + config.get('zillow', 'zillow_addr') + ":" +\
                                     config.get('zillow', 'zillow_port') +\
                                     config.get('zillow', 'zillow_path') + "?zws-id=" +\
                                     config.get('zillow', 'zillow_zws_id') + "&zpid=" +\
                                     config.get('zillow', 'zillow_zpid'))
    except Exception:
        retries += 1

        log.warn('Cannot connect to Zillow. Attempt %n of %n',\
                        retries, config.retries)

        if retries >= config.retries:
            log.Error('Cannot connect to Zillow. Exiting...')
            raise

        # Wait for the next poll intervall until we retry
        # also allows for configuration to get updated
        handler.sleep(config.getfloat('zillow', 'zillow_poll_interval', 3600))
        continue

    # Reset retries once we get a valid response
    retries = 0

    log.debug('Fetch data: %s', r.text)

    data = xml_to_dict(r.text)
    # Data Structure Documentation: http://www.zillow.com/howto/api/APIOverview.htm

    property_data = data['{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate']['response']['zestimate']
    local_data = data['{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate']['response']['localRealEstate']

    event = [{
        'name': 'zillow',
        'columns': ['valuation', '30daychange', 'rangehigh', 'rangelow', 'percentile', 'last-updated',
                    'region', 'regiontype', 'zindexValue'],
        'points': [[ property_data['amount'], property_data['valueChange'],
                     property_data['valuationRange']['high'],
                     property_data['valuationRange']['low'],
                     property_data['percentile'],
                     property_data['last-updated'],
                     local_data['region']['@name'],
                     local_data['region']['@type'],
                     local_data['region']['zindexValue']
                  ]]
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    handler.sleep(config.getfloat('zillow', 'zillow_poll_interval', 3600))
