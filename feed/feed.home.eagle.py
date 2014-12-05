#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.abspath('..'))

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import CtoF, mBtoiHg, mmtoin
from common.sheventhandler import shEventHandler
from dependencies.RainEagle import Eagle, to_epoch_1970

import logging as log
log.info('Starting feed for Rainforest Eagle gateway')

config = shConfig('~/.config/home/home.cfg')
handler = shEventHandler(config, config.getfloat('raineagle', 'eagle_poll_interval', 5))

retries = 0

while True:
    try:
        eg = Eagle(debug=0, addr=config.get('raineagle', 'eagle_addr'))
        break
    except Exception:
        retries += 1

        # Something went wrong authorizing the connection to the Eagle gateway
        log.warn( 'Cannot connect to Rainforest Eagle. Attemp %n of %n', i, config.retries )

        if retries >= config.retries:
            log.error( 'Unable to connect to Rainforest Eagle. Exiting...' )
            raise

        handler.sleep()

while True:
    raindata= eg.get_device_data()

    idemanddata = raindata['InstantaneousDemand']

    imultiplier = int(idemanddata['Multiplier'], 16)
    idivisor = int(idemanddata['Divisor'], 16)
    idemand = int(idemanddata['Demand'], 16)

    if idemand > 0x7FFFFFFF: idemand -= 0x100000000
    if imultiplier == 0 : imultiplier = 1
    if idivisor == 0 : idivisor = 1

    power = ((idemand * imultiplier) / float (idivisor))*1000
    amps = power/240

    csumdata = raindata['CurrentSummation']

    csummultiplier = int(csumdata['Multiplier'], 16)
    csumdivisor = int(csumdata['Divisor'], 16)
    csumreceived = int(csumdata['SummationReceived'], 16)
    csumdelivered = int(csumdata['SummationDelivered'], 16)

    if csummultiplier == 0 : csummultiplier = 1
    if csumdivisor == 0 : csumdivisor = 1

    received = ((csumreceived * csummultiplier) / float (csumdivisor))*1000
    delivered = ((csumdelivered * csummultiplier) / float (csumdivisor))*1000

    event = [{
        'name': 'power',
        'columns': [ 'whole_house_power', 'whole_house_amps', 'whole_house_received', 'whole_house_delivered' ],
        'points': [[ power, amps, received, delivered ]]
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    handler.sleep()
