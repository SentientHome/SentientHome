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
from common.sheventhandler import shEventHandler
from common.shutil import CtoF, m2toft2, boolify2int

from nest import Nest
# import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('nest', 'nest')
defaults['nest']['poll_interval'] = 60.0

with shApp('nest', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app, dedupe=True)

    nest = Nest(app.config.get('nest', 'nest_user'),
                app.config.get('nest', 'nest_pass'),
                access_token_cache_file=os.path.expanduser(
                    app.config.get('nest', 'nest_cache')),
                cache_ttl=9)

    while True:
        retries = 0

        # app.log.info(json.dumps(nest._status, sort_keys=True))
        # exit(1)

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
                                    'away'],
                        'points': [[structure.name,
                                    structure.postal_code,
                                    structure.country_code,
                                    structure.house_type,
                                    structure.renovation_date,
                                    (int)('%0.0f' % structure.structure_area),
                                    (int)('%0.0f' % m2toft2(structure.structure_area)),  # noqa
                                    structure.num_thermostats,
                                    structure.measurement_scale,
                                    structure.emergency_contact_description,
                                    structure.emergency_contact_type,
                                    structure.emergency_contact_phone,
                                    boolify2int(structure.dr_reminder_enabled),
                                    boolify2int(structure.enhanced_auto_away_enabled),  # noqa
                                    boolify2int(structure.eta_preconditioning_active),  # noqa
                                    boolify2int(structure.hvac_safety_shutoff_enabled),  # noqa
                                    boolify2int(structure.away)]]
                    }]

                    app.log.debug('Event data: %s' % event)

                    handler.postEvent(event, dedupe=True)

                    for device in structure.devices:

                        if device.away_temperature[1] is not None:
                            away_tempC = (float)('%0.1f' %
                                                 device.away_temperature[1])
                            away_tempF = (float)('%0.1f' % CtoF(
                                device.away_temperature[1]))
                        else:
                            away_tempC = 'Null'
                            away_tempF = 'Null'

                        event = [{
                            'name': 'nest_device',
                            'columns': ['name',
                                        'where',
                                        'serial',
                                        'last_ip',
                                        'local_ip',
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
                                        'last_connection',
                                        'error_code',
                                        'battery_level'],
                            'points': [[device.name,
                                        device.where,
                                        device.serial,
                                        device.last_ip,
                                        device.local_ip,
                                        device.mode,
                                        boolify2int(device.fan),
                                        (float)('%0.1f' % device.temperature),
                                        (float)('%0.1f' % CtoF(device.temperature)),  # noqa
                                        device.humidity,
                                        (float)('%0.1f' % device.target),
                                        (float)('%0.1f' % CtoF(device.target)),
                                        (float)('%0.1f' % device.away_temperature[0]),  # noqa
                                        (float)('%0.1f' % CtoF(device.away_temperature[0])),  # noqa
                                        away_tempC,
                                        away_tempF,
                                        boolify2int(device.hvac_ac_state),
                                        boolify2int(device.hvac_cool_x2_state),
                                        boolify2int(device.hvac_heater_state),
                                        boolify2int(device.hvac_aux_heater_state),  # noqa
                                        boolify2int(device.hvac_heat_x2_state),
                                        boolify2int(device.hvac_heat_x3_state),
                                        boolify2int(device.hvac_alt_heat_state),
                                        boolify2int(device.hvac_alt_heat_x2_state),  # noqa
                                        boolify2int(device.hvac_emer_heat_state),  # noqa
                                        boolify2int(device.online),
                                        device.last_connection,
                                        device.error_code,
                                        device.battery_level]]
                        }]

                        app.log.debug('Event data: %s' % event)

                        handler.postEvent(event, dedupe=True)

                    for protect in structure.protectdevices:

                        event = [{
                            'name': 'nestprotect_device',
                            'columns': ['name',
                                        'where',
                                        'description',
                                        'serial',
                                        'product_id',
                                        'software_version',
                                        'wifi_ip_address',
                                        'wifi_mac_address',
                                        'thread_mac_address',
                                        'auto_away',
                                        'battery_health_state',
                                        'battery_level',
                                        'capability_level',
                                        'certification_body',
                                        'co_blame_duration',
                                        'co_blame_threshold',
                                        'co_previous_peak',
                                        'co_sequence_number',
                                        'co_status',
                                        'component_als_test_passed',
                                        'component_co_test_passed',
                                        'component_heat_test_passed',
                                        'component_hum_test_passed',
                                        'component_led_test_passed',
                                        'component_pir_test_passed',
                                        'component_smoke_test_passed',
                                        'component_temp_test_passed',
                                        'component_us_test_passed',
                                        'component_wifi_test_passed',
                                        'creation_time',
                                        'gesture_hush_enable',
                                        'heads_up_enable',
                                        'home_alarm_link_capable',
                                        'home_alarm_link_connected',
                                        'home_alarm_link_type',
                                        'hushed_state',
                                        'latest_manual_test_cancelled',
                                        'latest_manual_test_end_utc_secs',
                                        'latest_manual_test_start_utc_secs',
                                        'line_power_present',
                                        'night_light_continuous',
                                        'night_light_enable',
                                        'ntp_green_led_enable',
                                        'replace_by_date_utc_secs',
                                        'smoke_sequence_number',
                                        'smoke_status',
                                        'steam_detection_enable',
                                        'wired_led_enable',
                                        'wired_or_battery'],
                            'points': [[protect.name,
                                        protect.where,
                                        protect.description,
                                        protect.serial,
                                        protect.product_id,
                                        protect.software_version,
                                        protect.wifi_ip_address,
                                        protect.wifi_mac_address,
                                        protect.thread_mac_address,
                                        boolify2int(protect.auto_away),
                                        protect.battery_health_state,
                                        protect.battery_level,
                                        protect.capability_level,
                                        protect.certification_body,
                                        protect.co_blame_duration,
                                        protect.co_blame_threshold,
                                        protect.co_previous_peak,
                                        protect.co_sequence_number,
                                        protect.co_status,
                                        boolify2int(protect.component_als_test_passed),  # noqa
                                        boolify2int(protect.component_co_test_passed),  # noqa
                                        boolify2int(protect.component_heat_test_passed),  # noqa
                                        boolify2int(protect.component_hum_test_passed),  # noqa
                                        boolify2int(protect.component_led_test_passed),  # noqa
                                        boolify2int(protect.component_pir_test_passed),  # noqa
                                        boolify2int(protect.component_smoke_test_passed),  # noqa
                                        boolify2int(protect.component_temp_test_passed),  # noqa
                                        boolify2int(protect.component_us_test_passed),  # noqa
                                        boolify2int(protect.component_wifi_test_passed),  # noqa
                                        protect.creation_time,
                                        boolify2int(protect.gesture_hush_enable),  # noqa
                                        boolify2int(protect.heads_up_enable),
                                        boolify2int(protect.home_alarm_link_capable),  # noqa
                                        boolify2int(protect.home_alarm_link_connected),  # noqa
                                        protect.home_alarm_link_type,
                                        boolify2int(protect.hushed_state),
                                        boolify2int(protect.latest_manual_test_cancelled),  # noqa
                                        protect.latest_manual_test_end_utc_secs,
                                        protect.latest_manual_test_start_utc_secs,  # noqa
                                        boolify2int(protect.line_power_present),
                                        boolify2int(protect.night_light_continuous),  # noqa
                                        boolify2int(protect.night_light_enable),
                                        boolify2int(protect.ntp_green_led_enable),  # noqa
                                        protect.replace_by_date_utc_secs,
                                        protect.smoke_sequence_number,
                                        protect.smoke_status,
                                        boolify2int(protect.steam_detection_enable),  # noqa
                                        boolify2int(protect.wired_led_enable),
                                        protect.wired_or_battery]]
                        }]

                        app.log.debug('Event data: %s' % event)

                        handler.postEvent(event, dedupe=True)

                break

            except (KeyError, AttributeError) as k:
                app.log.fatal('Error accessing Nest data. Exiting...')
                app.log.fatal(k)
                raise
            except Exception as e:
                retries += 1

                # Something went wrong communicating to the Nest service
                app.log.warn('Exception communicating with Nest. \
                              Attempt %s of %s' % (retries, app.retries))
                app.log.warn(e)
                raise(e)

                if retries >= app.retries:
                    app.log.fatal('Unable to connect to Nest. Exiting...')
                    app.log.fatal(e)
                    app.close(1)
                    exit(1)

                handler.sleep(app.retry_interval)

        handler.sleep()
