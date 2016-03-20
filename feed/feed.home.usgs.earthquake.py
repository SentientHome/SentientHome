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
from common.shutil import epoch2date

import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('usgs_quake', 'usgs_quake')
defaults['usgs_quake']['poll_interval'] = 10.0


def mapMetadata(metadata):

    event = [{
        'measurement': 'usgs.earthquake.metadata',     # Time Series Name
        'tags': {
            'title': metadata['title'],
            'api': metadata['api'],
            'status': metadata['status'],
        },
        'fields': {
            'generated': epoch2date(metadata['generated']/1000),
            'count': metadata['count']
        }
    }]

    return event


def mapFeature(feature):
    event = [{
        'measurement': 'usgs.earthquake.feature',      # Time Series Name
        'tags': {
            'type': feature['properties']['type'],
            'gtype': feature['geometry']['type'],
            'types': feature['properties']['types'],
            'magType': feature['properties']['magType'],
            'tsunami': feature['properties']['tsunami'],
            'code': feature['properties']['code'],
            'net': feature['properties']['net'],
            'nst': feature['properties']['nst'],
            'sources': feature['properties']['sources'],
            'alert': feature['properties']['alert'],
        },
        'fields': {
            'long': float(feature['geometry']['coordinates'][0]),
            'lat': float(feature['geometry']['coordinates'][1]),
            'depth': float(feature['geometry']['coordinates'][2]),
            'mag': float(feature['properties']['mag']),
            'felt': feature['properties']['felt'],
            'sig': feature['properties']['sig'],
            'dmin': feature['properties']['dmin'],
            'id': feature['id'],
            'status': feature['properties']['status'],
            'title': feature['properties']['title'],
            'place': feature['properties']['place'],
            'status': feature['properties']['status'],
            'time': epoch2date(feature['properties']['time']/1000),
            'updated': epoch2date(feature['properties']['updated']/1000),
            'tz': feature['properties']['tz'],
            'ids': feature['properties']['ids'],
        }
    }]

    fields = event[0]['fields']

    # Optional fields
    if feature['properties']['felt'] is not None:
        fields['felt'] = float(feature['properties']['felt'])

    if feature['properties']['gap'] is not None:
        fields['gap'] = float(feature['properties']['gap'])

    if feature['properties']['rms'] is not None:
        fields['rms'] = float(feature['properties']['rms'])

    if feature['properties']['mag'] is not None:
        fields['mag'] = float(feature['properties']['mag'])

    if feature['properties']['cdi'] is not None:
        fields['cdi'] = float(feature['properties']['cdi'])

    return event

with shApp('usgs_quake', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    path = app.config.get('usgs_quake', 'path')

    while True:
        # Get all earthquakes of the past hour
        r = handler.get(app.config.get('usgs_quake', 'addr') + path)
        data = json.loads(r.text)
        # app.log.debug('Raw data: %s' % r.text)

        event = mapMetadata(data['metadata'])
        app.log.debug('Event data: %s' % event)

        handler.postEvent(event, dedupe=True, batch=True)

        # Need to revser the order of incoming events as news are on top but we
        # need to process in the order they happened.
        features = data['features'][::-1]

        for feature in features:
            event = mapFeature(feature)
            app.log.debug('Event data: %s' % event)

            # dedupe automatically ignores events we have processed before
            handler.postEvent(event, dedupe=True, batch=True)

        # We reset the poll interval in case the configuration has changed
        handler.sleep()
