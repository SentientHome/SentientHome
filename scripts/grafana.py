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

import json

# Default settings
from cement.utils.misc import init_defaults

defaults = init_defaults('grafana', 'grafana')
defaults['grafana']['addr'] = 'http://192.168.99.100:3000'
defaults['grafana']['user'] = 'admin'
defaults['grafana']['pass'] = 'admin'
defaults['grafana']['debug'] = 1

with shApp('grafana', config_defaults=defaults) as app:
    app.run()

    handler = shEventHandler(app)

    try:
        # Get list of all Grafana dashboards
        r = handler.get(app.config.get('grafana', 'addr') +
                        '/api/search',
                        auth=(app.config.get('grafana', 'user'),
                              app.config.get('grafana', 'pass')))
    except Exception as e:
        # If event handler was unsuccessful retrying stop
        app.log.fatal(e)
        app.close(1)

    app.log.debug('response: %s' % r.text)

    dbs = json.loads(r.text)

    for db in dbs:
        app.log.debug('dashboard: %s' % db)

        try:
            # Get content of this dashboard
            r = handler.get(app.config.get('grafana', 'addr') +
                            '/api/dashboards/' + db['uri'],
                            auth=(app.config.get('grafana', 'user'),
                                  app.config.get('grafana', 'pass')))
        except Exception as e:
            # If event handler was unsuccessful retrying stop
            app.log.fatal(e)
            app.close(1)

        content = json.loads(r.text)
        # app.log.debug('response: %s' % r.text)

        filename = os.path.abspath('../dashboards/' + db['title'] + '.json')

        app.log.debug('filename: %s' % filename)
        # Write dashboard to file
        try:
            with open(filename, 'w') as out:
                out.write(json.dumps(content['dashboard'], sort_keys=True,
                          indent=2))
        except Exception as e:
            # Unable to write file
            app.log.error(e)
            pass
