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
from dependencies.nest_thermostat import Nest

import json, collections

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('nest', 'nest')
defaults['nest']['poll_interval'] = 60.0

with shApp('nest', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    retries = 0

    while True:
        try:
            nest = Nest(app.config.get('nest', 'nest_user'),\
                        app.config.get('nest', 'nest_pass'),\
                        access_token_cache_file=os.path.expanduser(\
                                        app.config.get('nest', 'nest_cache')))
            break
        except Exception:
            retries += 1

            # Something went wrong authorizing the connection to the NetAtmo service
            app.log.warn( 'Cannot connect to Nest. Attemp %n of %n' % (i, app.retries()) )

            if retries >= app.retries():
                app.log.fatal( 'Unable to connect to Nest. Exiting...' )
                app.close(1)

            handler.sleep(app.retry_interval())

    app.log.info( 'Nest Connection established.')

    # Create list of indoor locations for devices
    locations = collections.defaultdict(dict)

    for structure in nest._status['where']:
        for where in nest._status['where'][structure]['wheres']:
            locations[structure][where['where_id']] = where['name']

    print('Locations: ' + str(locations))

    # Now create list of devices
    devices = collections.defaultdict(dict)

    for structure in nest._status['structure']:
        for device in structure['devices']:
            devices[device]=locations[structure][device['where_id']]['name']

    print('Deviced:  ' + str(devices))


    while True:
        print ('=========================')
    #    print json.dumps(nest._status)
        print ('=========================')





    #        for subkey in nest._status[key].keys():
    #            print '----------------------------'
    #            print 'SubKey  : ' + subkey + ' = ' + str(nest._status[key][subkey])
    #            print 'Sub2keys: ' + str(nest._status[key][subkey].keys())

    #            for sub2key in nest._status[key][subkey].keys():
    #                print '++++++++++++++++++++++++++++'
    #                print 'Sub2Key  : ' + sub2key + ' = ' + str(nest._status[key][subkey][sub2key])
    #                try:
    #                    print 'Sub3keys: ' + str(nest._status[key][subkey][sub2key].keys())
    #                except Exception:
    #                    continue

    #    key = 'device'
    #    subkey = '02AA01AC18140042'

    #    print '----------------------------'
    #    print 'SubKey  : ' + subkey + ' = ' + str(nest._status[key][subkey])
    #    print 'Sub2keys: ' + str(nest._status[key][subkey].keys())

    #    for sub2key in nest._status[key][subkey].keys():
    #        print '++++++++++++++++++++++++++++'
    #        print 'Sub2Key  : ' + sub2key + ' = ' + str(nest._status[key][subkey][sub2key])
    #        try:
    #            print 'Sub3keys: ' + str(nest._status[key][subkey][sub2key].keys())
    #        except Exception:
    #            continue

        event = [{
            'name': 'nest',
            'columns': [ 'XXXX', 'YYYY' ],
            'points': [[ 1, 2 ]]
        }]

        app.log.debug('Event data: %s' % event)

    #    handler.postEvent(event)

        handler.sleep()
