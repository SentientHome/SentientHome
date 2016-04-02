#!/usr/local/bin/python3 -u
"""
    Author:     Oliver Ratzesberger <https://github.com/fxstein>
    Copyright:  Copyright (C) 2016 Oliver Ratzesberger
    License:    Apache License, Version 2.0
"""

# Make sure we have access to SentientHome commons
import os
import sys
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
except:
    exit(1)

# Sentient Home Application
from common.shapp import shApp
from common.shutil import xml_to_dict
from common.sheventhandler import shEventHandler

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('zillow', 'zillow')
defaults['zillow']['poll_interval'] = 3600.0

with shApp('zillow', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    while True:
        r = handler.get(app.config.get('zillow', 'zillow_addr') + ":" +
                        app.config.get('zillow', 'zillow_port') +
                        app.config.get('zillow', 'zillow_path') + "?zws-id=" +
                        app.config.get('zillow', 'zillow_zws_id') + "&zpid=" +
                        app.config.get('zillow', 'zillow_zpid'))
        # app.log.debug('Fetch data: %s' % r.text)

        data = xml_to_dict(r.text)
        app.log.debug('Raw data: %s' % data)

        # Data Structure Documentation:
        # http://www.zillow.com/howto/api/APIOverview.htm

        request_data = data[
            '{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate'][
            'response']
        property_data = data[
            '{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate'][
            'response']['zestimate']
        local_data = data[
            '{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate'][
            'response']['localRealEstate']

        event = [{
            'measurement': 'zillow',
            'tags': {
                'zpid': request_data['zpid'],
                'region': local_data['region']['@name'],
                'region_type': local_data['region']['@type'],
            },
            'fields': {
                'valuation': float(property_data['amount']),
                '30daychange': float(property_data['valueChange']),
                'range_high': float(property_data['valuationRange']['high']),
                'range_low': float(property_data['valuationRange']['low']),
                'percentile': int(property_data['percentile']),
                'zindexValue': float(local_data['region']
                                     ['zindexValue'].replace(',', '')),
                'last_updated': property_data['last-updated'],
            }
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        handler.sleep()
