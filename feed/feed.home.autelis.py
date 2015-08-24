#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home Application
from common.shapp import shApp
from common.shutil import xml_to_dict
from common.sheventhandler import shEventHandler

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('autelis', 'autelis')
defaults['autelis']['poll_interval'] = 10.0

with shApp('autelis', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    while True:
        try:
            r = handler.get(app.config.get('autelis', 'autelis_addr') +\
                             '/status.xml',\
                             auth=(app.config.get('autelis', 'autelis_user'),\
                             app.config.get('autelis', 'autelis_pass')))
                # Data Structure Documentation: http://www.autelis.com/wiki/index.php?
                # title=Pool_Control_(PI)_HTTP_Command_Reference
        except Exception as e:
            # If event handler was unsuccessful retrying stop
            app.log.fatal(e)
            app.close(1)

        app.log.debug('Fetch data: %s' % r.text)

        data = xml_to_dict(r.text)

        alldata = dict(list(data['response']['equipment'].items()) + \
                       list(data['response']['system'].items()) + \
                       list(data['response']['temp'].items()))

        event = [{
            'name':    'autelis', # Time Series Name
            'columns': list(alldata.keys()), # Keys
            'points':  [ list(alldata.values()) ] # Data points
        }]

        app.log.debug('Event data: %s' % event)

        handler.postEvent(event)

        # Wait for next poll interval
        handler.sleep()
