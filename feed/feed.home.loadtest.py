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

# Simple loadtest that 'fires' events as fast as possible

config = shConfig('~/.config/home/home.cfg', name='SentientHome LoadTest')
handler = shEventHandler(config, 10)

count = 0

while True:
    count += 1

    event = [{
        'name': 'loadtest', # Time Series Name
        'columns': ['count'], # Keys
        # time in milliseconds since epoch
        'points': [[count]] # Data points
    }]

    handler.postEvent(event)
