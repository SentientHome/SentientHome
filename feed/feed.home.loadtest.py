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

# Simple loadtest that 'fires' events as fast as possible

with shApp('loadtest') as app:
    app.run()
    handler = shEventHandler(app)

    count = 0

    while True:
        count += 1

        event = [{
            'measurement': 'loadtest',    # Time Series Name
            'fields': {
                'loadtest_count': count
                }
        }]

        handler.postEvent(event)
