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
import json
import hashlib

config = shConfig('~/.config/home/home.cfg',\
                    name='SMA Sunny Webbox Data Feed')
handler = shEventHandler(config,\
                         config.getfloat('sma_webbox', 'sma_webbox_poll_interval',\
                         30))

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


while True:
    # First check if there is a new password in the config
    try:
        passwd = config.get('sma_webbox', 'sma_webbox_pass')
    except:
        passwd = None
        pass

    if passwd != None:
        rpcrequest['passwd'] = hashlib.md5(passwd.encode('utf-8')).hexdigest()
    else:
        # If there is no password make sure we delete pior one
        rpcrequest.pop('passwd', None)

    try:
        log.debug('RPC request: %s', json.dumps(rpcrequest))

        r = handler.post('http://' + config.get('sma_webbox', 'sma_webbox_addr') +\
                             '/rpc', data='RPC=' + json.dumps(rpcrequest))

        log.debug('RPC response: %s', r.text)

        result = json.loads(r.text)

        # Assmble dynamic 'list' of values as a dict
        data = dict()
        for i in result['result']['overview']:
            try:
                # Normalize to W or Wh
                data[i['name']] = float(i['value'])*units[i['unit']]
            except ValueError:
                # Skip none numeric portions of the result
                pass

        event = [{
            'name':    shRegistry['smawebbox']['name'], # Time Series Name
            'columns': list(data.keys()), # Keys
            'points':  [ list(data.values()) ] # Data points
        }]

        log.debug('Event data: %s', event)

        handler.postEvent(event)
    except Exception as e:
        log.error('Error: %s', e)
        pass

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('sma_webbox', 'sma_webbox_poll_interval', 30))
