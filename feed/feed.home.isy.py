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
from common.shutil import flatten_dict, extract_tags
from common.sheventhandler import shEventHandler

# Add path to submodule dependencies.ISYlib-python
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                    '/../dependencies/ISYlib-python')
    from ISY.IsyClass import Isy
    from ISY.IsyEvent import ISYEvent
except:
    exit(1)

app = shApp('isy')
app.setup()
app.run()

handler = shEventHandler(app)

isy_addr = app.config.get('isy', 'isy_addr')
isy_user = app.config.get('isy', 'isy_user')
isy_pass = app.config.get('isy', 'isy_pass')

app.log.debug('Connecting to ISY controller @%s' % isy_addr, __name__)

try:
    isy = Isy(addr=isy_addr, userl=isy_user, userp=isy_pass)
except Exception as e:
    app.log.error('Unable to connect to ISY controller @%s' % isy_addr,
                  __name__)
    app.log.error(e)
    app.close()
    exit(1)

# Make sure we pre populate all internal isy structures
isy.load_nodes()


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
            str(data.pop('Event.action'))
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

    # Add node name to be used as a tag
    try:
        data['Event.node.name'] = isy._nodedict[data['Event.node']]['name']
    except KeyError:
        # Ok if it does not exist
        pass

    tags = extract_tags(data, ['Event.node', 'Event.node.name',
                        'Event.control'])

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
        server.subscribe(addr=isy_addr,
                         userl=isy_user,
                         userp=isy_pass)
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
