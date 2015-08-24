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
from common.shutil import CtoF, m2toft2, boolify, boolify2int

from nest import Nest

import json, collections

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('nest', 'nest')
defaults['nest']['poll_interval'] = 60.0

with shApp('nest', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    nest = Nest(app.config.get('nest', 'nest_user'),\
                app.config.get('nest', 'nest_pass'),\
                access_token_cache_file=os.path.expanduser(\
                                app.config.get('nest', 'nest_cache')))

    while True:
        retries = 0

        while True:
            try:
                for structure in nest.structures:
                    event = [{
                        'name': 'nest_structure',
                        'columns': ['name',
                                    'postal_code',
                                    'country_code',
                                    'house_type',
                                    'renovation_date',
                                    'structure_area_m2',
                                    'structure_area_ft2',
                                    'num_thermostats',
                                    'measurement_scale',
                                    'emergency_contact_description',
                                    'emergency_contact_type',
                                    'emergency_contact_phone',
                                    'dr_reminder_enabled',
                                    'enhanced_auto_away_enabled',
                                    'eta_preconditioning_active',
                                    'hvac_safety_shutoff_enabled',
                                    'away' ],
                        'points': [[structure.name,
                                    structure.postal_code,
                                    structure.country_code,
                                    structure.house_type,
                                    structure.renovation_date,
                                    (int)('%0.0f' % structure.structure_area),
                                    (int)('%0.0f' % m2toft2(structure.structure_area)),
                                    structure.num_thermostats,
                                    structure.measurement_scale,
                                    structure.emergency_contact_description,
                                    structure.emergency_contact_type,
                                    structure.emergency_contact_phone,
                                    boolify2int(structure.dr_reminder_enabled),
                                    boolify2int(structure.enhanced_auto_away_enabled),
                                    boolify2int(structure.eta_preconditioning_active),
                                    boolify2int(structure.hvac_safety_shutoff_enabled),
                                    boolify2int(structure.away) ]]
                    }]

                    app.log.debug('Event data: %s' % event)

                    handler.postEvent(event, dedupe=True)

                    for device in structure.devices:
                        event = [{
                            'name': 'nest_device',
                            'columns': ['name',
                                        'where',
                                        'mode',
                                        'fan',
                                        'temperature_C',
                                        'temperature_F',
                                        'humidity',
                                        'target_C',
                                        'target_F',
                                        'away_low_C',
                                        'away_low_F',
                                        'away_high_C',
                                        'away_high_F',
                                        'hvac_ac_state',
                                        'hvac_cool_x2_state',
                                        'hvac_heater_state',
                                        'hvac_aux_heater_state',
                                        'hvac_heat_x2_state',
                                        'hvac_heat_x3_state',
                                        'hvac_alt_heat_state',
                                        'hvac_alt_heat_x2_state',
                                        'hvac_emer_heat_state',
                                        'online',
                                        'last_ip',
                                        'local_ip',
                                        'last_connection',
                                        'error_code',
                                        'battery_level' ],
                            'points': [[device.name,
                                        device.where,
                                        device.mode,
                                        boolify2int(device.fan),
                                        (float)('%0.1f' % device.temperature),
                                        (float)('%0.1f' % CtoF(device.temperature)),
                                        device.humidity,
                                        (float)('%0.1f' % device.target),
                                        (float)('%0.1f' % CtoF(device.target)),
                                        (float)('%0.1f' % device.away_temperature[0]),
                                        (float)('%0.1f' % CtoF(device.away_temperature[0])),
                                        (float)('%0.1f' % device.away_temperature[1]),
                                        (float)('%0.1f' % CtoF(device.away_temperature[1])),
                                        boolify2int(device.hvac_ac_state),
                                        boolify2int(device.hvac_cool_x2_state),
                                        boolify2int(device.hvac_heater_state),
                                        boolify2int(device.hvac_aux_heater_state),
                                        boolify2int(device.hvac_heat_x2_state),
                                        boolify2int(device.hvac_heat_x3_state),
                                        boolify2int(device.hvac_alt_heat_state),
                                        boolify2int(device.hvac_alt_heat_x2_state),
                                        boolify2int(device.hvac_emer_heat_state),
                                        boolify2int(device.online),
                                        device.last_ip,
                                        device.local_ip,
                                        device.last_connection,
                                        device.error_code,
                                        device.battery_level ]]
                        }]

                        app.log.debug('Event data: %s' % event)

                        handler.postEvent(event, dedupe=True)

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

                # Something went wrong communicating to the Nest service
                app.log.warn('Exception communicaing with Nest. Attempt %s of %s' % (retries, app.retries))
                app.log.warn(e)

                if retries >= app.retries:
                    app.log.fatal( 'Unable to connect to Nest. Exiting...' )
                    app.log.fatal(e)
                    app.close(1)

                handler.sleep(app.retry_interval)

        handler.sleep()
