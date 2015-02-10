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
import time

# Simple tracer that 'fires' events on a predefined interval

config = shConfig('~/.config/home/home.cfg', name='SentientHome Tracer')
handler = shEventHandler(config, config.getfloat('sentienthome', 'tracer_interval', 10))

count = 0

while True:
    count += 1

    event = [{
        'name': 'tracer', # Time Series Name
        'columns': ['time', 'count'], # Keys
        # time in milliseconds since epoch
        'points': [[time.time()*1000, count]] # Data points
    }]

    log.debug('Event data: %s', event)

    handler.postEvent(event)

    # We reset the poll interval in case the configuration has changed
    handler.sleep(config.getfloat('sentienthome', 'tracer_interval', 10))
