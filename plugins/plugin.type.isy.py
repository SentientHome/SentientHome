#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from collections import defaultdict, deque

from cement.core import hook
from cement.utils.misc import init_defaults

sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                '/../dependencies/ISYlib-python')

from ISY.IsyClass import Isy

defaults = init_defaults('plugin.isy')


def extend_app(app):

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
        return

    # extend the event engine app object with an ``isy`` member
    app.extend('isy', isy)

    app.log.info('Succeful ISY Plugin registration', __name__)


def event_state(app, event_type, event):
    app.log.debug('event_state() Event: %s %s' %
                  (event_type, event), __name__)
    try:
        if event_type == 'isy':
            # Initialize state event cache if it does not exist yet
            if not app._memory.state[event_type]:
                app._memory.state[event_type] = defaultdict(deque)

            # Populate state memory
            state = dict()
            state['time'] = event['shtime1']

            state['control'] = event['Event.control']
            state['action'] = event['Event.action']

            actions = ['DON', 'DFON', 'DOF', 'DFOF', 'ST', 'OL',
                       'RR', 'BMAN', 'SMAN', 'DIM', 'BRT']

            if state['control'] in actions:
                # Initialize state event cache if it does not exist yet
                if not isinstance(app._memory.state[event_type]
                                  [event['Event.node']], deque):
                    app._memory.state[event_type][event['Event.node']] =\
                        deque(maxlen=100)

                app.log.info('Node: %s Data: %s' %
                             (event['Event.node'], state), __name__)
                app._memory.state[event_type][event['Event.node']].\
                    appendleft(state)
    except Exception as e:
        app.log.error('Error appending state: %s' % e, __name__)


def process_event(app, event_type, event):
    app.log.debug('process_event() Event: %s %s' %
                  (event_type, event), __name__)

    # if etype == 'isy' and event['Event.node'] == '24 0 93 1':
    #     app.log.debug('!!!!!!!!!!FOUNTAIN!!!!!!!!!!!')
    # elif etype == 'isy' and event['Event.node'] == '29 14 86 1':
    #     app.log.debug('!!!!!!!!!!LIVING - WINDOW - OUTLET!!!!!!!!!!!')
    # elif etype == 'isy' and state['control'] == 'DON':
    #     app.log.debug('Node: %s TURNED ON!!!!!!!!!!!!!!!!' %
    #                   event['Event.node'])
    # elif etype == 'isy' and state['control'] == 'ST':
    #     app.log.debug('Node: %s SET TARGET!!!!!!!!!!!!!!!' %
    #                   event['Event.node'])
    #
    # if etype == 'ubnt.mfi.sensor':
    #     # Slow test workload for async task
    #     app.log.debug('mFi Sensor event: %s' % event)
    #     # log.debug('Pause for 10 sec')
    #     # yield from asyncio.sleep(10)
    #     # log.debug('Back from sleep')
    #
    # # Test mFi Sensor rule
    # if etype == 'ubnt.mfi.sensor' and event['label'] == 'Well.Well.Pump':
    #     if event['amps'] < 21 and event['amps'] > 15:
    #         # Turn off the well pump for set amount of time
    #         app.log.info('!!!!!!!! WELL PUMP SAVER ACTION !!!!!!!!!')
    #
    #         # First put pump to sleep
    #         well_pump = app.isy.get_node("Well - Well Pump")
    #         if well_pump:
    #             well_pump.off()
    #             # yield from asyncio.sleep(2)
    #             # well_pump.off()
    #             #
    #             # # Then schedule wakeup at a later time
    #             # yield from asyncio.sleep(900)
    #             # well_pump.on()
    #             # yield from asyncio.sleep(2)
    #             # well_pump.on()


def load(app):
    hook.register('post_run', extend_app)
    hook.register('event_state', event_state)
    hook.register('process_event', process_event)

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
