#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2016 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.shutil import numerify, extract_tags
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

with shApp('eagle', config_defaults=defaults) as app:
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

    network_command = '<LocalCommand>\n\
                            <Name>get_network_info</Name>\n\
                            <MacId>' + device_macid + '</MacId>\n\
                       </LocalCommand>'

    usage_command = '<LocalCommand>\n\
                        <Name>get_usage_data</Name>\n\
                        <MacId>' + device_macid + '</MacId>\n\
                    </LocalCommand>'

    while True:
        try:
            n = handler.post(app.config.get('eagle', 'eagle_addr') +
                             '/cgi-bin/cgi_manager', data=network_command)
            u = handler.post(app.config.get('eagle', 'eagle_addr') +
                             '/cgi-bin/cgi_manager', data=usage_command)
        except Exception as e:
            # If event handler was unsuccessful retrying stop
            app.log.fatal(e)
            app.close(1)

        app.log.debug('Network data: %s' % n.text)
        app.log.debug('Usage data: %s' % u.text)

        networkdata = dict((k, numerify(v)) for k, v in
                           json.loads(n.text).items())

        usagedata = dict((k, numerify(v)) for k, v in
                         json.loads(u.text).items())

        # Normalize to W or Wh
        try:
            demand = float(usagedata['demand']) *\
                units[usagedata['demand_units']]
            received = float(usagedata['summation_received']) *\
                units[usagedata['summation_units']]
            delivered = float(usagedata['summation_delivered']) *\
                units[usagedata['summation_units']]
            link_strength = int(networkdata['network_link_strength'], base=16)
        except ValueError:
            app.log.error('Unsupport demand or summation units')
            pass
        except KeyError as e:
            app.log.error('Missing Key: %s' % e)
            pass

        try:
            amps = demand/(int)(app.config.get('eagle', 'voltage'))
        except ZeroDivisionError as e:
            app.log.error(e)

        tags = extract_tags(networkdata, ['network_meter_mac_id',
                                          'network_ext_pan_id',
                                          'network_short_addr',
                                          'network_status',
                                          'network_channel'])
        event = [{
            'measurement': 'eagle',
            'tags': tags,
            'fields': {
                'demand': demand,
                'amps': amps,
                'summation_received': received,
                'summation_delivered': delivered,
                'network_link_strength': link_strength
                }
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Wait for next poll interval
        handler.sleep()
