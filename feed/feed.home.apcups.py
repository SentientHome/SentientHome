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
from common.shutil import numerify, CtoF

from pysnmp.entity.rfc3413.oneliner import cmdgen

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('apcups', 'apcups')
defaults['apcups']['poll_interval'] = 10.0

# Feed APC UPS data

# Map intersting OIDs to names and descriptions for human readability
# Dont want to carry a multi megabyte MIB file for just a few values
# desc currently only used to make the code better documented
oids = {
    '1.3.6.1.4.1.318.1.1.1.2.1.1.0': {'name': 'upsstatus',
                                      'desc': 'UPS Status'},
    '1.3.6.1.4.1.318.1.1.1.2.2.1.0': {'name': 'batcap',
                                      'desc': 'Battery Capacity [%]'},
    '1.3.6.1.4.1.318.1.1.1.2.2.2.0': {'name': 'battemp',
                                      'desc': 'Battery Temp [C]'},
    '1.3.6.1.4.1.318.1.1.1.2.2.3.0': {'name': 'runtime',
                                      'desc': 'Runtime [ms]'},
    '1.3.6.1.4.1.318.1.1.1.3.2.1.0': {'name': 'linevolt',
                                      'desc': 'Line Voltage [V]'},
    '1.3.6.1.4.1.318.1.1.1.3.2.2.0': {'name': 'linemaxvolt',
                                      'desc': 'Line Max Voltage [V]'},
    '1.3.6.1.4.1.318.1.1.1.3.2.3.0': {'name': 'lineminvolt',
                                      'desc': 'Line Min Voltage [V]'},
    '1.3.6.1.4.1.318.1.1.1.3.2.4.0': {'name': 'infreq',
                                      'desc': 'Input Freq [Hz]'},
    '1.3.6.1.4.1.318.1.1.1.4.2.1.0': {'name': 'outvolt',
                                      'desc': 'Output Voltage [V]'},
    '1.3.6.1.4.1.318.1.1.1.4.2.2.0': {'name': 'outfreq',
                                      'desc': 'Output Freq [Hz]'},
    '1.3.6.1.4.1.318.1.1.1.4.2.3.0': {'name': 'outload',
                                      'desc': 'Output Load [%]'},
    '1.3.6.1.4.1.318.1.1.1.4.2.4.0': {'name': 'outcurrent',
                                      'desc': 'Output Current [A]'},
    '1.3.6.1.4.1.318.1.1.1.7.2.3.0': {'name': 'lasttestres',
                                      'desc': 'Last Test Result'},
    '1.3.6.1.4.1.318.1.1.1.7.2.4.0': {'name': 'lasttestdate',
                                      'desc': 'Last Test Date'},
}

with shApp('apcups', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    try:
        cmdGen = cmdgen.CommandGenerator()

        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
            cmdgen.CommunityData('public'),
            cmdgen.UdpTransportTarget((
                app.config.get('apcups', 'apcups_addr'), 161)),
            cmdgen.MibVariable('SNMPv2-MIB', 'sysDescr', 0),
            lookupNames=True, lookupValues=True
        )
    except Exception as e:
        app.log.fatal('Unhandled exception: %s' % e)
        app.close(1)

    # Check for errors and print out results
    if errorIndication:
        app.log.error(errorIndication)
    elif errorStatus:
        app.log.error(errorStatus)
    else:
        for name, val in varBinds:
            app.log.info('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

    data = dict()

    while True:

        try:
            errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
                cmdgen.CommunityData('public'),
                cmdgen.UdpTransportTarget((
                    app.config.get('apcups', 'apcups_addr'), 161)), *oids
            )
        except Exception as e:
            app.log.error('Unhandled exception: %s' % e)

        # Check for errors and assemble results
        if errorIndication:
            app.log.error(errorIndication)
        elif errorStatus:
            app.log.error(errorStatus)
        else:
            for name, val in varBinds:
                app.log.debug('%s = %s (%s)' % (name, val,
                                                oids[str(name)]['desc']))
                if oids[str(name)]['name'] == 'runtime':
                    # Convert runtime into seconds
                    data[oids[str(name)]['name']] = int(numerify(str(val))/100)
                elif oids[str(name)]['name'] == 'battemp':
                    data[oids[str(name)]['name']] = numerify(str(val))
                    # Also provide temp in F
                    data['battempf'] = CtoF(data[oids[str(name)]['name']])
                else:
                    data[oids[str(name)]['name']] = numerify(str(val))

            event = [{
                'name': 'apcups',  # Time Series Name
                'columns': list(data.keys()),  # Keys
                'points': [list(data.values())]  # Data points
            }]

            app.log.debug('Event data: %s', event)

            handler.postEvent(event)

        # We reset the poll interval in case the configuration has changed
        handler.sleep()
