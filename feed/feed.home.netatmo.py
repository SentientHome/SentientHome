#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import CtoF, mBtoiHg, mmtoin
from common.sheventhandler import shEventHandler
from dependencies.netatmo import lnetatmo

import logging as log
log.info('Starting feed for Netatmo climate data')

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config, config.getfloat('autelis', 'netatmo_poll_interval', 10))

netatmo_unique = config.getint('netatmo', 'netatmo_unique', 1)

retries = 0

while True:
    try:
        authorization = lnetatmo.ClientAuth(\
                            clientId = config.get('netatmo', 'netatmo_client_id'),
                            clientSecret = config.get('netatmo', 'netatmo_client_secret'),
                            username = config.get('netatmo', 'netatmo_user'),
                            password = config.get('netatmo', 'netatmo_pass') )
        break
    except Exception:
        retries += 1

        # Something went wrong authorizing the connection to the NetAtmo service
        log.warn( 'Cannot connect to NetAtmo. Attemp %n of %n', i, config.retries )

        if retries >= config.retries:
            log.error( 'Unable to connect to Netatmo. Exiting...' )
            raise

        handler.sleep(config.getfloat('autelis', 'netatmo_poll_interval', 10))

log.info( 'NetAtmo Connection established.')

while True:
    devList = lnetatmo.DeviceList(authorization)

    # Loop through all stations in the account
    for station in devList.stations.keys():

        station_name = devList.stations[station]['station_name']
        devData = devList.lastData(station=station_name)

        # Optional metric to imperal conversions
        # Modified event data contains bot metric and imperal
        # Not all sensors have all metrics to convert
        for key in devData.keys():
            try:
                devData[key]['TemperatureF']=CtoF(devData[key]['Temperature'])
                devData[key]['min_tempF']=CtoF(devData[key]['min_temp'])
                devData[key]['max_tempF']=CtoF(devData[key]['max_temp'])
            except Exception:
                pass

            try:
                devData[key]['PressureiHg']=mBtoiHg(devData[key]['Pressure'])
            except Exception:
                pass

            try:
                devData[key]['sum_rain_1in']=mmtoin(devData[key]['sum_rain_1'])
                devData[key]['sum_rain_24in']=mmtoin(devData[key]['sum_rain_24'])
            except Exception:
                pass

            # If module names are unique across stations we can use them as our key
            # Ff not we have to prepend the station name
            if netatmo_unique == 1:
                devData[key]['Module']=key
            else:
                devData[key]['Module']=station_name + '.' + key

            event = [{
                'name': 'netatmo',
                'columns': list(devData[key].keys()),
                'points': [ list(devData[key].values()) ]
            }]

            log.debug('Event data: %s', event)

            handler.postEvent(event)

    handler.sleep(config.getfloat('autelis', 'netatmo_poll_interval', 10))
