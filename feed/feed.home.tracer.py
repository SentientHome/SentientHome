#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2016 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.sheventhandler import shEventHandler

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
            'measurement': 'tracer',
            'fields': {
                'tracer_time': time.time(),
                'tracer_count': count
                }
        }]

        app.log.info('Event data: %s' % event)

        handler.postEvent(event)

        # Wait until next tracer intervall
        handler.sleep()
