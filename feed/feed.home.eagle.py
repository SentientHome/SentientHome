#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.shutil import numerify
from common.sheventhandler import shEventHandler

import json

units = {
    'W':    1,
    'kW':   1000,
    'MW':   1000*1000,
    'Wh':   1,
    'kWh':  1000,
    'MWh':  1000*1000,
}

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('eagle', 'eagle')
defaults['eagle']['poll_interval'] = 5.0
defaults['eagle']['voltage'] = 240

with shApp('autelis', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    command = '<LocalCommand>\n\
                    <Name>get_device_list</Name>\n\
               </LocalCommand>'

    r = handler.post(app.config.get('eagle', 'eagle_addr') +
                     '/cgi-bin/cgi_manager', data=command)
    app.log.debug('Fetch data: %s' % r.text)

    device = json.loads(r.text)
    device_macid = device['device_mac_id[0]']

    command = '<LocalCommand>\n\
                    <Name>get_usage_data</Name>\n\
                    <MacId>' + device_macid + '</MacId>\n\
               </LocalCommand>'

    while True:
        try:
            r = handler.post(app.config.get('eagle', 'eagle_addr') +
                             '/cgi-bin/cgi_manager', data=command)
        except Exception as e:
            # If event handler was unsuccessful retrying stop
            app.log.fatal(e)
            app.close(1)

        app.log.debug('Fetch data: %s' % r.text)

        devicedata = dict((k, numerify(v)) for k, v in
                          json.loads(r.text).items())

        # Normalize to W or Wh
        try:
            power = float(devicedata['demand']) *\
                units[devicedata['demand_units']]
            received = float(devicedata['summation_received']) *\
                units[devicedata['summation_units']]
            delivered = float(devicedata['summation_delivered']) *\
                units[devicedata['summation_units']]
        except ValueError:
            app.log.error('Unsupport demand or summation units')
            pass

        try:
            amps = power/(int)(app.config.get('eagle', 'voltage'))
        except ZeroDivisionError as e:
            app.log.error(e)

        event = [{
            'name': 'power',
            'columns': ['whole_house_power', 'whole_house_amps',
                        'whole_house_received', 'whole_house_delivered'],
            'points': [[power, amps, received, delivered]]
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Wait for next poll interval
        handler.sleep()
