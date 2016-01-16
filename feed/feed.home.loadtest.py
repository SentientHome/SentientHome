#!/usr/local/bin/python3 -u
"""
    Author:     Oliver Ratzesberger <https://github.com/fxstein>
    Copyright:  Copyright (C) 2016 Oliver Ratzesberger
    License:    Apache License, Version 2.0
"""

# Make sure we have access to SentientHome commons
import os
import sys
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
except:
    exit(1)

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
