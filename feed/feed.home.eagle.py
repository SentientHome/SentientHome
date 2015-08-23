#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.shutil import numerify
from common.sheventhandler import shEventHandler

import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('eagle', 'eagle')
defaults['eagle']['poll_interval'] = 5.0
defaults['eagle']['voltage'] = 240

with shApp('autelis', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    command =  '<LocalCommand>\n\
                    <Name>get_device_list</Name>\n\
                </LocalCommand>'

    r = handler.post(app.config.get('eagle', 'eagle_addr') +\
                     '/cgi-bin/cgi_manager', data=command)
    app.log.debug('Fetch data: %s' % r.text)

    device = json.loads(r.text)
    device_macid = device['device_mac_id[0]']

    command =  '<LocalCommand>\n\
                    <Name>get_usage_data</Name>\n\
                    <MacId>' + device_macid + '</MacId>\n\
                </LocalCommand>'

    while True:
        try:
            r = handler.post(app.config.get('eagle', 'eagle_addr') +\
                             '/cgi-bin/cgi_manager', data=command)
        except Exception as e:
            # If event handler was unsuccessful retrying stop
            app.log.fatal(e)
            app.close(1)

        app.log.debug('Fetch data: %s' % r.text)

        devicedata = dict((k, numerify(v)) for k, v in json.loads(r.text).items())

        if devicedata['demand_units'] == 'W':
            power = devicedata['demand']
        elif devicedata['demand_units'] == 'kW':
            power = devicedata['demand'] * 1000
        elif devicedata['demand_units'] == 'MW':
            power = devicedata['demand'] * 1000 * 1000
        else:
            app.log.error( 'Unsupport demand units: %s' % devicedata['demand_units'] )

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
            app.log.error( 'Unsupport summation units: %s' % devicedata['summation_units'] )

        try:
            amps = power/(int)(app.config.get('eagle', 'voltage'))
        except ZeroDivisionError as e:
            app.log.error(e)

        event = [{
            'name': 'power',
            'columns': [ 'whole_house_power', 'whole_house_amps', 'whole_house_received', 'whole_house_delivered' ],
            'points': [[ power, amps, received, delivered ]]
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Wait for next poll interval
        handler.sleep()
