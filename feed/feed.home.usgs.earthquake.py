#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.sheventhandler import shEventHandler

import logging as log

log.info('Starting SentientHome feed for USGS earthquake data')

import requests
import json
# For checkpoint file
import pickle

config = shConfig('~/.config/home/home.cfg')
# default to 5 min polls - the frequency the USGS update the feed
handler = shEventHandler(config, config.getfloat('usgs_quake', 'usgs_quake_poll_interval', 300))

retries = 0

# Initial poll - most likely a day if the increments are hourly data
# We do this to catchup on events in case the feed was down for some time
path = config.get('usgs_quake', 'usgs_quake_init_path')

# Empty event cache - Needed to dedup incoming events if we have processed them
events = list()

(xxx, tmpfilename) = os.path.split(__file__)
checkpoint_filename = '/tmp/' + tmpfilename + '.json'
# See if we can restore the event cache from a previsous checkpoint
try:
    with open(checkpoint_filename, 'rb') as f:
        # The protocol version used is detected automatically, so we do not
        # have to specify it.
        events = pickle.load(f)
except (OSError, EOFError) as e:
    log.warning('Unable to read checkpoint file: %s', checkpoint_filename)
    pass

while True:
    try:
        # Get all earthquakes of the past hour
        r = requests.get('http://' + config.get('usgs_quake', 'usgs_quake_addr') +\
                         path)
    except Exception:
        retries += 1

        log.warn('Cannot connect to USGS earthquake feed. Attempt %s of %s',\
                        retries, config.retries)

        if retries >= config.retries:
            log.Error('Cannot connect to USGS earthquake feed. Exiting...')
            raise

        # Wait for the next poll intervall until we retry
        # also allows for configuration to get updated
        handler.sleep(config.getfloat('usgs_quake', 'usgs_quake_poll_interval', 300))
        continue

    # Reset retries once we get a valid response
    retries = 0

    #log.debug('Fetch data: %s', r.text)

    data = json.loads(r.text)

    m = data['metadata']

    event = [{
        'name': 'usgs.earthquake.metadata', # Time Series Name
        'columns': ['title', 'count', 'generated', 'api', 'status'], # Keys
        'points': [[ m['title'], m['count'], m['generated'],\
                     m['api'], m['status'] ]] # Data points
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    features = data['features']

    newevent = False

    for f in features:

        event = [{
            'name': 'usgs.earthquake.feature', # Time Series Name
            'columns': ['id', 'long', 'lat', 'depth', 'mag', 'type'\
                        'magtype', 'tz', 'felt', 'place', 'status'\
                        'gap', 'dmin', 'rms', 'ids', 'title', 'types'\
                        'cdi', 'net', 'nst', 'sources', 'alert', 'time'\
                        'tsunami', 'code', 'sig'
                        ], # Keys
            'points': [[ f['id'],\
                         f['geometry']['coordinates'][0],\
                         f['geometry']['coordinates'][1],\
                         f['geometry']['coordinates'][2],\
                         f['properties']['mag'],\
                         f['properties']['type'],\
                         f['properties']['magType'],\
                         f['properties']['tz'],\
                         f['properties']['felt'],\
                         f['properties']['place'],\
                         f['properties']['status'],\
                         f['properties']['gap'],\
                         f['properties']['dmin'],\
                         f['properties']['rms'],\
                         f['properties']['ids'],\
                         f['properties']['title'],\
                         f['properties']['types'],\
                         f['properties']['cdi'],\
                         f['properties']['net'],\
                         f['properties']['nst'],\
                         f['properties']['sources'],\
                         f['properties']['alert'],\
                         f['properties']['time'],\
                         f['properties']['tsunami'],\
                         f['properties']['code'],\
                         f['properties']['sig']
                          ]] # Data points
        }]

        if event in events:
            log.debug('Surpressing duplicate event id: %s', event[0]['points'][0][0])
        else:
            log.debug('Event data: %s', event)

            newevent = True
            events.insert(0, event)

            # TODO: Purge events older than x hours

            handler.postEvent(event)

        log.debug('Event Cache Count: %s', len(events))

    # If new events have been added to our cache, checkpoint it to file
    if newevent == True:
        try:
            with open(checkpoint_filename, 'wb') as f:
                # Pickle the 'data' dictionary using the highest protocol available.
                pickle.dump(events, f, pickle.HIGHEST_PROTOCOL)
        except OSError:
            log.warning('Unable to write checkpoint file: %s', checkpoint_filename)
            pass

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('usgs_quake', 'usgs_quake_poll_interval', 300))

    # Reset poll path before looping with latest setting
    path = config.get('usgs_quake', 'usgs_quake_path')
