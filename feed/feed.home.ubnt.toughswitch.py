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
from common.sheventhandler import shEventHandler
from common.shutil import boolify

import requests
import json


def mapPort(switch, config, port, data):
    event = [{
        'measurement': 'ubnt.toughswitch',
        'tags': {
            'switch': switch,
            'port': port,
            'portname': config['switch.port.%s.name' % port],
            'duplex': boolify(config['switch.port.%s.duplex' % port]),
            'trunk.status': boolify(config['switch.port.%s.trunk.status' %
                                           port]),
            'switch.jumboframes': boolify(config['switch.jumboframes']),
            },
        'fields': {
            }
    }]

    fields = event[0]['fields']
    tags = event[0]['tags']

    for key in data.keys():
        if key == 'stats':
            for stat in data[key].keys():
                try:
                    fields[stat] = float(data[key][stat])
                except ValueError:
                    fields[stat] = data[key][stat]
        else:
            tags[key] = data[key]

    return event


# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('ubnt_toughswitch', 'ubnt_toughswitch')
defaults['ubnt_toughswitch']['poll_interval'] = 5.0

with shApp('ubnt_toughswitch', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    retries = 0
    sessions = []

    addresses = app.config.get('ubnt_toughswitch', 'addr').split(', ')
    switch_port = app.config.get('ubnt_toughswitch', 'port')
    switch_user = app.config.get('ubnt_toughswitch', 'user')
    passwords = app.config.get('ubnt_toughswitch', 'pass').split(', ')
    switch_verify_ssl = app.config.get('ubnt_toughswitch', 'verify_ssl')

    # Setup sessions for each switch
    for i in range(len(addresses)):
        sessions.append(requests.session())

    for i in range(len(addresses)):
        while True:
            try:
                r = sessions[i].get(addresses[i] + ':' + switch_port +
                                    '/login.cgi',
                                    verify=(int)(switch_verify_ssl))
                app.log.debug('Response: %s' % r)

                r = sessions[i].post(addresses[i] + ':' + switch_port +
                                     '/login.cgi',
                                     params={'username': switch_user,
                                             'password': passwords[i],
                                             'uri': ' /stats'},
                                     verify=(int)(switch_verify_ssl))

                app.log.debug('Response: %s' % r)

                break
            except Exception as e:
                retries += 1

                # Something went wrong authorizing the connection to ubnt ts
                app.log.warn(e)
                app.log.warn('Cannot connect to ToughSwitch. Attemp %s of %s' %
                             (retries, app.retries))

                if retries >= app.retries:
                    app.log.fatal(e)
                    app.log.fatal('Unable to connect to ToughSwitch. Exiting..')
                    app.close(1)

                handler.sleep(app.retry_interval)

    while True:

        for i in range(len(addresses)):

            # Get ToughSwitch statistics
            retries = 0

            while True:
                try:
                    r = sessions[i].get(addresses[i] + ':' + switch_port +
                                        '/getcfg.cgi',
                                        verify=(int)(switch_verify_ssl))
                    if r.text is not '' and r.text is not None:
                        config = json.loads(r.text)

                        r = sessions[i].get(addresses[i] + ':' + switch_port +
                                            '/stats',
                                            verify=(int)(switch_verify_ssl))
                        if r.text is not '' and r.text is not None:
                            data = json.loads(r.text)
                            break

                    handler.sleep(app.retry_interval)

                except Exception as e:
                    retries += 1

                    # Something went wrong connecting to the ubnt mfi service
                    app.log.warn(e)
                    app.log.warn('Cannot connect. Attemp %s of %s' %
                                 (retries, app.retries))

                    if retries >= app.retries:
                        app.log.fatal(e)
                        app.log.fatal('Unable to connect. Exiting...')
                        app.close(1)

                    handler.sleep(app.retry_interval)

            app.log.debug('Config: %s' % json.dumps(config, sort_keys=True))
            app.log.debug('Data: %s' % json.dumps(data, sort_keys=True))

            switch = addresses[i].replace('https://', '')

            for port in range(1, 9):

                event = mapPort(switch, config, port, data['stats'][str(port)])

                app.log.debug('Event: %s' % event)
                # dedupe automatically ignores events we have processed before
                # This is where the dedupe magic happens. The event handler has
                # deduping built in and keeps an in-memory cache of events of
                # the past ~24h for that. In this case only changed switch data
                # points will get emitted and stored
                handler.postEvent(event, dedupe=True, batch=True)

        # We reset the poll interval in case the configuration has changed
        handler.sleep()
