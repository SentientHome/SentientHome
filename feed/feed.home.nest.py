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
from common.shutil import CtoF, m2toft2

from nest import Nest

import json, collections

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('nest', 'nest')
defaults['nest']['poll_interval'] = 60.0

with shApp('nest', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    nest = Nest(app.config.get('nest', 'nest_user'),\
                app.config.get('nest', 'nest_pass'),\
                access_token_cache_file=os.path.expanduser(\
                                app.config.get('nest', 'nest_cache')))

    while True:
        retries = 0

        while True:
            try:
                for structure in nest.structures:
                    print ('Structure   : %s' % structure.name)
                    print (' ZIP        : %s' % structure.postal_code)
                    print (' Country    : %s' % structure.country_code)
                    print (' dr_reminder_enabled            : %s' % structure.dr_reminder_enabled)
                    print (' emergency_contact_description  : %s' % structure.emergency_contact_description)
                    print (' emergency_contact_type         : %s' % structure.emergency_contact_type)
                    print (' enhanced_auto_away_enabled     : %s' % structure.enhanced_auto_away_enabled)
                    print (' eta_preconditioning_active     : %s' % structure.eta_preconditioning_active)
                    print (' house_type                     : %s' % structure.house_type)
                    print (' hvac_safety_shutoff_enabled    : %s' % structure.hvac_safety_shutoff_enabled)
                    print (' num_thermostats                : %s' % structure.num_thermostats)
                    print (' measurement_scale              : %s' % structure.measurement_scale)
                    print (' renovation_date                : %s' % structure.renovation_date)
                    print (' structure_area                 : %0.0fm2 %0.0fft2' % (structure.structure_area,m2toft2(structure.structure_area)))

                    print ('    Away    : %s' % structure.away)
                    print ('    Devices :')

                    for device in structure.devices:
                        print ('        Name : %s' % device.name)
                        print ('        Where: %s' % device.where)
                        print ('            Mode     : %s' % device.mode)
                        print ('            Fan      : %s' % device.fan)
                        print ('            Temp     : %0.0fC %0.0fF' % (device.temperature, CtoF(device.temperature)))
                        print ('            Humidity : %0.0f%%' % (device.humidity))
                        print ('            Target   : %0.0fC %0.0fF' % (device.target, CtoF(device.target)))
                        print ('            Away Heat: %0.0fC %0.0fF' % (device.away_temperature[0], CtoF(device.away_temperature[0])))
                        print ('            Away Cool: %0.0fC %0.0fF' % (device.away_temperature[1], CtoF(device.away_temperature[1])))

                        print ('            hvac_ac_state         : %s' % device.hvac_ac_state)
                        print ('            hvac_cool_x2_state    : %s' % device.hvac_cool_x2_state)
                        print ('            hvac_heater_state     : %s' % device.hvac_heater_state)
                        print ('            hvac_aux_heater_state : %s' % device.hvac_aux_heater_state)
                        print ('            hvac_heat_x2_state    : %s' % device.hvac_heat_x2_state)
                        print ('            hvac_heat_x3_state    : %s' % device.hvac_heat_x3_state)
                        print ('            hvac_alt_heat_state   : %s' % device.hvac_alt_heat_state)
                        print ('            hvac_alt_heat_x2_state: %s' % device.hvac_alt_heat_x2_state)
                        print ('            hvac_emer_heat_state  : %s' % device.hvac_emer_heat_state)

                        print ('            online                : %s' % device.online)
                        print ('            last_ip               : %s' % device.last_ip)
                        print ('            local_ip              : %s' % device.local_ip)
                        print ('            last_connection       : %s' % device.last_connection)

                        print ('            error_code            : %s' % device.error_code)
                        print ('            battery_level         : %s' % device.battery_level)

                break
            except KeyError as k:
                app.log.fatal('Key error accessing Nest data. Exiting...')
                app.log.fatal(k)
                raise
            except AttributeError as a:
                app.log.fatal('Attribute error accessing Nest data. Exiting...')
                app.log.fatal(a)
                raise
            except Exception as e:
                retries += 1

                # Something went wrong authorizing the connection to the Nest service
                app.log.warn('Exception communicaing with Nest. Attempt %s of %s' % (retries, app.retries))
                app.log.warn(e)

                raise

                if retries >= app.retries:
                    app.log.fatal( 'Unable to connect to Nest. Exiting...' )
                    app.log.fatal(e)
                    app.close(1)

                handler.sleep(app.retry_interval)

        event = [{
            'name': 'nest',
            'columns': [ 'XXXX', 'YYYY' ],
            'points': [[ 1, 2 ]]
        }]

        app.log.debug('Event data: %s' % event)

    #    handler.postEvent(event)

        handler.sleep()
