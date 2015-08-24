#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.sheventhandler import shEventHandler
from common.shutil import CtoF

import requests
import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('ubnt_mfi', 'ubnt_mfi')
defaults['ubnt_mfi']['poll_interval'] = 5.0

with shApp('ubnt_mfi', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    retries = 0

    # Setup session and login
    session = requests.session()

    while True:
        try:
            r = session.post(app.config.get('ubnt_mfi', 'ubnt_mfi_addr') + ':' +\
                        app.config.get('ubnt_mfi', 'ubnt_mfi_port') + '/login',\
                      {'username': app.config.get('ubnt_mfi', 'ubnt_mfi_user'),\
                       'password': app.config.get('ubnt_mfi', 'ubnt_mfi_pass'),\
                       'login':'Login'},\
                        verify=(int)(app.config.get('ubnt_mfi', 'ubnt_mfi_verify_ssl')))
            break
        except Exception as e:
            retries += 1

            # Something went wrong authorizing the connection to the ubnt mfi service
            app.log.warn(e)
            app.log.warn('Cannot connect to MFI. Attemp %s of %s' % (retries, app.retries))

            if retries >= app.retries:
                app.log.fatal(e)
                app.log.fatal('Unable to connect to MFI. Exiting...')
                app.close(1)

            handler.sleep(app.retry_interval)

    while True:
        # Get all sensors and their most current data
        # We could do this multiple times per second if needed to drive down latency
        # This is just the polling part, we then auto dedupe the data to only
        # emit changed sensor values to the engine and event store
        retries = 0

        while True:
            try:
                r = session.get(app.config.get('ubnt_mfi', 'ubnt_mfi_addr') + ':' +\
                                app.config.get('ubnt_mfi', 'ubnt_mfi_port') + '/api/v1.0/list/sensors',\
                                verify=(int)(app.config.get('ubnt_mfi', 'ubnt_mfi_verify_ssl')))
                break
            except Exception as e:
                retries += 1

                # Something went wrong connecting to the ubnt mfi service
                app.log.warn(e)
                app.log.warn('Cannot connect to MFI. Attemp %s of %s' % (retries, app.retries))

                if retries >= app.retries:
                    app.log.fatal(e)
                    app.log.fatal('Unable to connect to MFI. Exiting...')
                    app.close(1)

                handler.sleep(app.retry_interval)

        data = json.loads(r.text)

        for sensor in data['data']:
            # If there is a temerature reading also create a Farenheit version
            # We have to do this since InfluxDB and/or Grafana cant do the most
            # simplistic math...
            try:
                sensor['temperatureF'] = CtoF(sensor['temperature'])
            except:
                pass

            event = [{
                'name': 'ubnt.mfi.sensor', # Time Series Name
                'columns': list(sensor.keys()), # Keys
                'points': [list(sensor.values())] # Data points
            }]

            app.log.debug('Event: %s' % event)
            # dedupe automatically ignores events we have processed before
            # This is where the dedupe magic happens. The event handler has deduping
            # built in and keeps an in-memory cache of events of the past 24h for that
            # In this case only changed sensor data points will get emitted and stored
            handler.postEvent(event, dedupe=True)

        # We reset the poll interval in case the configuration has changed
        handler.sleep()
