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
from common.shregistry import shRegistry

import time

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('shTracer', 'shTracer')
defaults['shTracer']['poll_interval'] = 10.0

# Simple tracer that 'fires' events on a predefined interval

with shApp('shTracer', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)
    # Simple Tracer counter
    count = 0

    while True:
        count += 1

        event = [{
            'name': shRegistry['tracer']['name'], # Time Series Name
            'columns': ['tracertime', 'count'], # Keys
            # time in milliseconds since epoch
            'points': [[time.time()*1000, count]] # Data points
        }]

        app.log.info('Event data: %s' % event)

        handler.postEvent(event)

        # Wait until next tracer intervall
        handler.sleep()
