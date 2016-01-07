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
from common.shutil import CtoF, mBtoiHg, mmtoin, epoch2date
from common.sheventhandler import shEventHandler

# Default settings
from cement.utils.misc import init_defaults

import json
import time

_API_URL = 'https://api.netatmo.net/'
_OAUTH2_REQ = _API_URL + 'oauth2/token'
_GETSTATION_REQ = _API_URL + 'api/getstationsdata?access_token='

defaults = init_defaults('netatmo', 'netatmo')
defaults['netatmo']['poll_interval'] = 60.0


def mapStation(station):
    return [{
        'measurement': 'netatmo.station',
        'tags': {
            'id': station['_id'],
            'station_name': station['station_name'],
            'module_name': station['module_name'],
            'firmware': int(station['firmware']),
            'type': station['type'],
            },
        'fields': {
            'wifi_status': int(station['wifi_status']),
            }
    },
    {
        'measurement': 'netatmo.module',
        'tags': {
            'id': station['_id'],
            'station_name': station['station_name'],
            'module_name': station['module_name'],
            'firmware': int(station['firmware']),
            'type': station['type'],
            'date_max_temp':
                epoch2date(station['dashboard_data']['date_max_temp']),
            'date_min_temp':
                epoch2date(station['dashboard_data']['date_min_temp']),
            # 'pressure_trend': station['dashboard_data']['pressure_trend'],
            # 'temp_trend': station['dashboard_data']['temp_trend'],
            },
        'fields': {
            'co2_calibrating': station['co2_calibrating'],
            'pressure': station['dashboard_data']['Pressure'],
            'abs_pressure': station['dashboard_data']['AbsolutePressure'],
            'pressurei': mBtoiHg(station['dashboard_data']['Pressure']),
            'abs_pressurei': mBtoiHg(station['dashboard_data']['AbsolutePressure']),  # noqa
            'co2': int(station['dashboard_data']['CO2']),
            'humidity': int(station['dashboard_data']['Humidity']),
            'noise': int(station['dashboard_data']['Noise']),
            'temp': station['dashboard_data']['Temperature'],
            'max_temp': station['dashboard_data']['max_temp'],
            'min_temp': station['dashboard_data']['min_temp'],
            'tempf': CtoF(station['dashboard_data']['Temperature']),
            'max_tempf': CtoF(station['dashboard_data']['max_temp']),
            'min_tempf': CtoF(station['dashboard_data']['min_temp']),
            }
    }]


def mapModule(station, module):

    # This part of the event mapping is constant accross module types
    event = [{
        'measurement': 'netatmo.module',
        'tags': {
            'id': module['_id'],
            'station_name': station['station_name'],
            'module_name': module['module_name'],
            'firmware': int(module['firmware']),
            'type': module['type'],
            },
        'fields': {
            'battery_vp': int(module['battery_vp']),
            'rf_status': int(module['rf_status']),
            }
    }]

    tags = event[0]['tags']
    fields = event[0]['fields']
    dashboard = module['dashboard_data']

    # Now add module type specific mappings
    if module['type'] in ['NAModule1', 'NAModule4']:  # Outdoor & Indoor
        tags['date_max_temp'] = epoch2date(dashboard['date_max_temp']),
        tags['date_min_temp'] = epoch2date(dashboard['date_min_temp']),

        fields['humidity'] = int(dashboard['Humidity'])
        fields['temp'] = dashboard['Temperature']
        fields['max_temp'] = dashboard['max_temp']
        fields['min_temp'] = dashboard['min_temp']
        fields['tempf'] = CtoF(dashboard['Temperature'])
        fields['max_tempf'] = CtoF(dashboard['max_temp'])
        fields['min_tempf'] = CtoF(dashboard['min_temp'])

    elif module['type'] == 'NAModule3':  # Rain
        fields['rain'] = dashboard['Rain']
        fields['sum_rain_1'] = dashboard['sum_rain_1']
        fields['sum_rain_24'] = dashboard['sum_rain_24']
        fields['raini'] = mmtoin(dashboard['Rain'])
        fields['sum_rain_1i'] = mmtoin(dashboard['sum_rain_1'])
        fields['sum_rain_24i'] = mmtoin(dashboard['sum_rain_24'])

    if module['type'] == 'NAModule4':  # Additional for Indoor
        # tags['temp_trend'] = dashboard['temp_trend']
        fields['co2'] = int(dashboard['CO2'])

    return event


with shApp('netatmo', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    # Start the Oauth2 dance...
    oauth2Params = {
        'grant_type': 'password',
        'client_id': app.config.get('netatmo', 'netatmo_client_id'),
        'client_secret': app.config.get('netatmo', 'netatmo_client_secret'),
        'username': app.config.get('netatmo', 'netatmo_user'),
        'password': app.config.get('netatmo', 'netatmo_pass'),
        'scope': 'read_station'
        }

    r = handler.post(_OAUTH2_REQ, data=oauth2Params)
    oauth2 = json.loads(r.text)
    oauth2['expiration'] = int(oauth2['expire_in'] + time.time())

    # We are authorized (for now)
    app.log.info('NetAtmo Connection established.')

    while True:
        time1 = time.time()

        # Check if we need to renew our Oauth2 tokens
        if oauth2['expiration'] < time1:
            renewParams = {
                'grant_type': 'refresh_token',
                'refresh_token': oauth2['refresh_token'],
                'client_id': oauth2Params['client_id'],
                'client_secret': oauth2Params['client_secret']
                }

            r = handler.post(_OAUTH2_REQ, data=oauth2Params)
            renew = json.loads(r.text)
            oauth2['access_token'] = renew['access_token']
            oauth2['refresh_token'] = renew['refresh_token']
            oauth2['expiration'] = int(renew['expire_in'] + time.time())

        # Now get the data we are really interested in
        r = handler.get(_GETSTATION_REQ + oauth2['access_token'])

        data = json.loads(r.text, parse_int=float)

        # app.log.debug('Device data: %s' % json.dumps(data, sort_keys=True))

        time2 = time.time()

        event = [{
            'measurement': 'netatmo.service',
            'tags': {
                'status': data['status']
                },
            'fields': {
                'time_elapsed': float(time2-time1),
                'time_exec': data['time_exec']
                }
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Loop through all stations in the account
        try:
            for station in data['body']['devices']:
                event = mapStation(station)

                app.log.debug('Event data: %s' % event)

                handler.postEvent(event, batch=True)

                for module in station['modules']:
                    event = mapModule(station, module)

                    app.log.debug('Event data: %s' % event)

                    handler.postEvent(event, batch=True)
        except KeyError as e:
            app.log.warn('Key Error: %s' % e)
            pass

        handler.sleep()
