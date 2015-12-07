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
from common.sheventhandler import shEventHandler

import json
import hashlib

units = {
    'W':    1,
    'kW':   1000,
    'MW':   1000*1000,
    'Wh':   1,
    'kWh':  1000,
    'MWh':  1000*1000,
    'lbs':  1,
    'kg':   1,
    'Hz':   1,
    'h':    1,
    'A':    1,
    'kA':   1000,
    'degC': 1,
    'degF': 1,
    'Ohm':  1,
    'kOhm': 1000,
    'MOhm': 1000*1000,
    'V':     1,
    'kV':    1000,
    '':      1
}

names = {
    'Backup State':     'backup_state',
    'CO2 saved':        'co2_saved',
    'Error':            'error',
    'E-Total':          'energy_total',
    'Fac':              'f_ac',
    'Grid Type':        'grid_type',
    'h-On':             'h_on',
    'h-Total':          'h_total',
    'Iac':              'i_ac',
    'Inv.TmpVal':       'inverter_temp',
    'Ipv':              'i_pv',
    'Mode':             'mode',
    'Pac':              'power_ac',
    'Pcb.TmpVal':       'pcb_temp',
    'Power On':         'power_on',
    'Riso':             'r_iso',
    'Serial Number':    'serial',
    'Vac':              'v_ac',
    'Vpv':              'v_pv',
}

rpcRequest = {
    'version':  '1.0',
    'id':       '1',
    'format':   'JSON',
}


def mapPlantOverview(plant_overview):
    event = [{
        'measurement': 'smawebbox.plant_overview',
        'tags': {
            'id': plant_overview['id'],
            'proc': plant_overview['proc'],
            'version': plant_overview['version'],
            },
        'fields': {
            }
    }]

    fields = event[0]['fields']
    for i in plant_overview['result']['overview']:
        try:
            # Normalize to W or Wh
            fields[i['name']] = float(i['value'])*units[i['unit']]
        except ValueError:
            # Skip none numeric portions of the result
            pass

        if i['name'] == 'OpStt':
            event[0]['tags']['mode'] = i['value']

    return event


def mapProcessData(device_data, process_data):

    events = []
    devices = process_data['result']['devices']

    for device in devices:
        event = {
            'measurement': 'smawebbox.process_data',
            'tags': {
                'id': process_data['id'],
                'proc': process_data['proc'],
                'version': process_data['version'],
                },
            'fields': {
            }
        }

        at_least_one = False
        fields = event['fields']
        tags = event['tags']
        for channel in device['channels']:
            if channel['name'] in ['Backup State', 'Error', 'Grid Type',
                                   'Mode', 'Serial Number']:
                # tags
                tags[names[channel['name']]] = channel['value']
            else:
                # fields
                try:
                    fields[names[channel['name']]] = float(channel['value']) *\
                        units[channel['unit']]
                    at_least_one = True
                except ValueError:
                    # Skip none numeric portions of the result
                    pass

        if at_least_one is True:
            events.append(event)

    return events

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

        if passwd is not None:
            rpcRequest['passwd'] = hashlib.md5(
                passwd.encode('utf-8')).hexdigest()
        else:
            # If there is no password make sure we delete pior one
            rpcRequest.pop('passwd', None)

        webbox_addr = app.config.get('sma_webbox', 'sma_webbox_addr')

        # Get and map Plant Overview data
        rpcRequest['proc'] = 'GetPlantOverview'
        app.log.debug('RPC request: %s' % json.dumps(rpcRequest))

        r = handler.post(webbox_addr +
                         '/rpc', data='RPC=' + json.dumps(rpcRequest))
        app.log.debug('RPC response: %s' % r.text)

        event = mapPlantOverview(json.loads(r.text))
        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Get and map Devices data
        rpcRequest['proc'] = 'GetDevices'
        app.log.debug('RPC request: %s' % json.dumps(rpcRequest))

        r = handler.post(webbox_addr +
                         '/rpc', data='RPC=' + json.dumps(rpcRequest))
        app.log.debug('RPC response: %s' % r.text)
        device_data = json.loads(r.text)

        # Process Data of those devices
        rpcRequest['proc'] = 'GetProcessData'
        rpcRequest['params'] = {'devices': []}

        for i in device_data['result']['devices']:
            rpcRequest['params']['devices'].append({'key': i['key']})

        app.log.debug('RPC request: %s' % json.dumps(rpcRequest))

        r = handler.post(webbox_addr +
                         '/rpc', data='RPC=' + json.dumps(rpcRequest))
        app.log.debug('RPC response: %s' % r.text)

        event = mapProcessData(device_data, json.loads(r.text))
        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        handler.sleep()
