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
from common.shutil import flatten_dict, extract_tags
from common.sheventhandler import shEventHandler

# Add path to submodule dependencies.ISYlib-python
sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                '/../dependencies/ISYlib-python')
from ISY.IsyEvent import ISYEvent

app = shApp('isy')
app.setup()
app.run()

handler = shEventHandler(app)


# Realtime event feeder
def eventFeed(*arg):

    # Flatten dict and turn embedded structure into dot notation
    data = flatten_dict(arg[0])

    # specify a few specific datatypes
    try:
        data['Event.action'] = float(data['Event.action'])
    except KeyError:
        # Ok if it does not exist
        pass
    except ValueError:
        data['Event.actionstring'] =\
            str(data.pop('Event.actionstring'))
        pass

    try:
        data['Event.eventInfo.value'] = float(data['Event.eventInfo.value'])
    except KeyError:
        # Ok if it does not exist
        pass
    except ValueError:
        data['Event.eventInfo.valuestring'] =\
            str(data.pop('Event.eventInfo.value'))
        pass

    tags = extract_tags(data, ['Event-sid', 'Event.node', 'Event.control'])

    event = [{
        'measurement': 'isy',
        'tags': tags,
        'fields': data
    }]

    app.log.debug('Event data: %s' % event)

    handler.postEvent(event)

# Setup ISY socket listener
# Be aware: Even though we are able to update the config at runtime
# we do not take down the web socket subscription once established
server = ISYEvent()

retries = 0

while True:
    try:
        server.subscribe(addr=app.config.get('isy', 'isy_addr'),
                         userl=app.config.get('isy', 'isy_user'),
                         userp=app.config.get('isy', 'isy_pass'))
        break
    except Exception as e:
        retries += 1

        app.log.warn(e)
        app.log.warn('Cannot connect to ISY. Attempt %n of %n',
                     retries, app.config.retries)

        if retries >= app.config.retries:
            app.log.Fatal('Unable to connect to ISY. Exiting...')
            app.close(1)

        # Wait for the next poll intervall until we retry
        # also allows for configuration to get updated
        handler.sleep()
        continue


server.set_process_func(eventFeed, "")

try:
    server.events_loop()   # no return
except KeyboardInterrupt:
    app.log.info('Exiting...')

app.close()
