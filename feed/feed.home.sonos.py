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
from common.sheventhandler import shEventHandler

import soco
import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('sonos', 'sonos')
defaults['sonos']['poll_interval'] = 10.0


def mapXXXX(xxxxx):
    event = [{
        'measurement': 'sonos',
        'tags': {
            },
        'fields': {
            }
    }]

    # fields = event[0]['fields']
    # tags = event[0]['tags']

    return event


with shApp('sonos', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    retries = 0

    while True:
        try:
            # Connect to Sonos Controller

            break
        except Exception as e:
            retries += 1

            # Something went wrong authorizing the connection to Sonos
            app.log.warn(e)
            app.log.warn('Cannot connect to Sonos. Attemp %s of %s' %
                         (retries, app.retries))

            if retries >= app.retries:
                app.log.fatal(e)
                app.log.fatal('Unable to connect to Sonos. Exiting...')
                app.close(1)

            handler.sleep(app.retry_interval)

    while True:
        # Get all Sonos data...
        retries = 0

        while True:
            try:

                break
            except Exception as e:
                retries += 1

                # Something went wrong connecting to the ubnt mfi service
                app.log.warn(e)
                app.log.warn('Cannot connect to Sonos. Attemp %s of %s' %
                             (retries, app.retries))

                if retries >= app.retries:
                    app.log.fatal(e)
                    app.log.fatal('Unable to connect to Sonos. Exiting...')
                    app.close(1)

                handler.sleep(app.retry_interval)

        # data = json.loads(r.text)
        # app.log.debug('Data: %s' % r.text)
        #
        # for sensor in data['data']:
        #
        #     event = mapSonos(sensor)
        #
        #     app.log.debug('Event: %s' % event)
        #
        #     handler.postEvent(event, dedupe=True, batch=True)

        # We reset the poll interval in case the configuration has changed
        handler.sleep()
