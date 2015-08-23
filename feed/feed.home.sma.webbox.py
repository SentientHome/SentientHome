#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.shutil import xml_to_dict
from common.sheventhandler import shEventHandler
from common.shregistry import shRegistry

import json
import hashlib

units = {
    'W':    1,
    'kW':   1000,
    'MW':   1000*1000,
    'Wh':   1,
    'kWh':  1000,
    'MWh':  1000*1000,
}

rpcrequest = {
    'version':  '1.0',
    'proc':     'GetPlantOverview',
    'id':       '1',
    'format':   'JSON',
}

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('sma_webbox', 'sma_webbox')
defaults['sma_webbox']['poll_interval'] = 30.0

with shApp('sma_webbox', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    while True:
        # First check if there is a new password in the config
        try:
            passwd = app.config.get('sma_webbox', 'sma_webbox_pass')
        except:
            passwd = None
            pass

        if passwd != None:
            rpcrequest['passwd'] = hashlib.md5(passwd.encode('utf-8')).hexdigest()
        else:
            # If there is no password make sure we delete pior one
            rpcrequest.pop('passwd', None)

        app.log.debug('RPC request: %s' % json.dumps(rpcrequest))

        r = handler.post(app.config.get('sma_webbox', 'sma_webbox_addr') +\
                         '/rpc', data='RPC=' + json.dumps(rpcrequest))

        app.log.debug('RPC response: %s' % r.text)

        result = json.loads(r.text)

        # Assmble dynamic dict of values
        data = dict()
        for i in result['result']['overview']:
            try:
                # Normalize to W or Wh
                data[i['name']] = float(i['value'])*units[i['unit']]

                # Perform optinal simplified efficency calculation
                if i['name'] == 'GriPwr':
                    try:
                        data['shSolarEff'] = data[i['name']] /\
                            (config.get('sma_webbox', 'sma_webbox_total_panels')\
                            * config.get('sma_webbox', 'sma_webbox_panel_rating'))
                        app.log.debug('Solar System Efficency: %s%' % (data['shSolarEff']*100))

                        data['shPanelPwr'] = data[i['name']] /\
                            (config.get('sma_webbox', 'sma_webbox_total_panels'))
                        app.log.debug('Solar Power per Panel: %sW' % data['shPanelPwr'])
                    except:
                        # Skip if optional settings are not set
                        pass

            except ValueError:
                # Skip none numeric portions of the result
                pass

        event = [{
            'name':    shRegistry['smawebbox']['name'], # Time Series Name
            'columns': list(data.keys()), # Keys
            'points':  [ list(data.values()) ] # Data points
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        handler.sleep()
