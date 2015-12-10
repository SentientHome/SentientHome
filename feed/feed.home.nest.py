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
from common.shutil import CtoF, m2toft2, boolify, epoch2date

from nest import Nest
import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('nest', 'nest')
defaults['nest']['poll_interval'] = 60.0


def mapStructure(structure):
    event = [{
        'measurement': 'nest.structure',
        'tags': {
            'name': structure.name,
            'postal_code': structure.postal_code,
            'country_code': structure.country_code,
            'house_type': structure.house_type,
            'renovation_date': structure.renovation_date,
            'measurement_scale': structure.measurement_scale,
            'emergency_contact_description': structure.emergency_contact_description,  # noqa
            'emergency_contact_type': structure.emergency_contact_type,
            'emergency_contact_phone': structure.emergency_contact_phone,
            'structure_area_m2': ('%0.0f' % structure.structure_area),
            'structure_area_ft2': ('%0.0f' % m2toft2(structure.structure_area)),  # noqa
            },
        'fields': {
            'dr_reminder_enabled': boolify(structure.dr_reminder_enabled),
            'enhanced_auto_away_enabled': boolify(structure.enhanced_auto_away_enabled),  # noqa
            'eta_preconditioning_active': boolify(structure.eta_preconditioning_active),  # noqa
            'hvac_safety_shutoff_enabled': boolify(structure.hvac_safety_shutoff_enabled),  # noqa
            'away': boolify(structure.away)
            }
    }]

    # Optional fields
    try:
        event[0]['fields']['num_thermostats'] = int(structure.num_thermostats)
    except ValueError:
        pass

    return event


def mapThermostat(thermostat):
    if thermostat.away_temperature[1] is not None:
        away_tempC = (float)('%0.1f' % thermostat.away_temperature[1])
        away_tempF = (float)('%0.1f' % CtoF(thermostat.away_temperature[1]))
    else:
        away_tempC = 'Null'
        away_tempF = 'Null'

    event = [{
        'measurement': 'nest.thermostat',
        'tags': {
            'name': thermostat.name,
            'where': thermostat.where,
            'serial': thermostat.serial,
            'last_ip': thermostat.last_ip,
            'local_ip': thermostat.local_ip,
            'mode': thermostat.mode,
            'last_connection': epoch2date(thermostat.last_connection/1000),
            'error_code': thermostat.error_code,
            },
        'fields': {
            'fan': boolify(thermostat.fan),
            'temperature_C': (float)('%0.1f' % thermostat.temperature),
            'temperature_F': (float)('%0.1f' % CtoF(thermostat.temperature)),
            'humidity': thermostat.humidity,
            'target_C': (float)('%0.1f' % thermostat.target),
            'target_F': (float)('%0.1f' % CtoF(thermostat.target)),
            'away_low_C': (float)('%0.1f' % thermostat.away_temperature[0]),
            'away_low_F': (float)('%0.1f' % CtoF(thermostat.away_temperature[0])),  # noqa
            'away_high_C': away_tempC,
            'away_high_F': away_tempF,
            'hvac_ac_state': boolify(thermostat.hvac_ac_state),
            'hvac_cool_x2_state': boolify(thermostat.hvac_cool_x2_state),
            'hvac_heater_state': boolify(thermostat.hvac_heater_state),
            'hvac_aux_heater_state': boolify(thermostat.hvac_aux_heater_state),
            'hvac_heat_x2_state': boolify(thermostat.hvac_heat_x2_state),
            'hvac_heat_x3_state': boolify(thermostat.hvac_heat_x3_state),
            'hvac_alt_heat_state': boolify(thermostat.hvac_alt_heat_state),
            'hvac_alt_heat_x2_state': boolify(thermostat.hvac_alt_heat_x2_state),  # noqa
            'hvac_emer_heat_state': boolify(thermostat.hvac_emer_heat_state),
            'online': boolify(thermostat.online),
            'battery_level': float(thermostat.battery_level)
            }
    }]

    return event


def mapProtect(protect):
    event = [{
        'measurement': 'nest.protect',
        'tags': {
            'name': protect.name,
            'where': protect.where,
            'description': protect.description,
            'serial': protect.serial,
            'product_id': protect.product_id,
            'software_version': protect.software_version,
            'wifi_ip_address': protect.wifi_ip_address,
            'wifi_mac_address': protect.wifi_mac_address,
            'thread_mac_address': protect.thread_mac_address,
            'battery_health_state': protect.battery_health_state,
            'capability_level': protect.capability_level,
            'certification_body': protect.certification_body,
            'creation_time': epoch2date(protect.creation_time/1000),
            'home_alarm_link_type': protect.home_alarm_link_type,
            'latest_manual_test_end_utc_secs': protect.latest_manual_test_end_utc_secs,  # noqa
            'latest_manual_test_start_utc_secs': protect.latest_manual_test_start_utc_secs,  # noqa
            'replace_by_date_utc_secs': epoch2date(protect.replace_by_date_utc_secs),  # noqa
            'smoke_sequence_number': protect.smoke_sequence_number,
            'smoke_status': protect.smoke_status,
            'wired_or_battery': protect.wired_or_battery
            },
        'fields': {
            'auto_away': boolify(protect.auto_away),
            'battery_level': float(protect.battery_level),
            'co_blame_duration': protect.co_blame_duration,
            'co_blame_threshold': protect.co_blame_threshold,
            'co_previous_peak': protect.co_previous_peak,
            'co_sequence_number': protect.co_sequence_number,
            'co_status': protect.co_status,
            'component_als_test_passed': boolify(protect.component_als_test_passed),  # noqa
            'component_co_test_passed': boolify(protect.component_co_test_passed),  # noqa
            'component_heat_test_passed': boolify(protect.component_heat_test_passed),  # noqa
            'component_hum_test_passed': boolify(protect.component_hum_test_passed),  # noqa
            'component_led_test_passed': boolify(protect.component_led_test_passed),  # noqa
            'component_pir_test_passed': boolify(protect.component_pir_test_passed),  # noqa
            'component_smoke_test_passed': boolify(protect.component_smoke_test_passed),  # noqa
            'component_temp_test_passed': boolify(protect.component_temp_test_passed),  # noqa
            'component_us_test_passed': boolify(protect.component_us_test_passed),  # noqa
            'component_wifi_test_passed': boolify(protect.component_wifi_test_passed),  # noqa
            'gesture_hush_enable': boolify(protect.gesture_hush_enable),
            'heads_up_enable': boolify(protect.heads_up_enable),
            'home_alarm_link_capable': boolify(protect.home_alarm_link_capable),
            'home_alarm_link_connected': boolify(protect.home_alarm_link_connected),  # noqa
            'hushed_state': boolify(protect.hushed_state),
            'latest_manual_test_cancelled': boolify(protect.latest_manual_test_cancelled),  # noqa
            'line_power_present': boolify(protect.line_power_present),
            'night_light_continuous': boolify(protect.night_light_continuous),  # noqa
            'night_light_enable': boolify(protect.night_light_enable),
            'ntp_green_led_enable': boolify(protect.ntp_green_led_enable),  # noqa
            'steam_detection_enable': boolify(protect.steam_detection_enable),  # noqa
            'wired_led_enable': boolify(protect.wired_led_enable),
            }
    }]

    return event


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

        # Retry loop for Nest communications
        while True:
            try:
                # Loop through Nest structures aka homes
                for structure in nest.structures:
                    event = mapStructure(structure)
                    app.log.debug('Event data: %s' % event)

                    handler.postEvent(event, dedupe=True, batch=True)

                    # Loop through all Thermostats
                    for thermostat in structure.devices:
                        event = mapThermostat(thermostat)
                        app.log.debug('Event data: %s' % event)

                        handler.postEvent(event, dedupe=True, batch=True)

                    # Loop through all Protects
                    for protect in structure.protectdevices:
                        event = mapProtect(protect)
                        app.log.debug('Event data: %s' % event)

                        handler.postEvent(event, dedupe=True, batch=True)

                # Break retry loop if we arrived here without exception
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
