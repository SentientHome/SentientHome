#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import time
from cement.core import hook


def process_event(app, event_type, event):
    app.log.debug('process_event() Event: %s %s' %
                  (event_type, event), __name__)

    try:
        if event_type == 'isy' and event['Event.node'] is not None:
            # Lookup name for easy rules coding
            nodename = app.isy._nodedict[event['Event.node']]['name']

            app.log.warn('ISY Node Event: %s %s: %s' %
                         (event['Event.node'], nodename, event), __name__)

            if nodename == 'Master - Lights' and\
                    event['Event.control'] == 'DON':
                app.log.error('Auto Off for: %s %s' %
                              (event['Event.node'], nodename), __name__)
                time.sleep(5)

                app.isy[event['Event.node']].off()
    except Exception as e:
        app.log.error(e)

    # if event_type == 'isy' and event['Event.node'] == '24 0 93 1':
    #     app.log.warn('!!!!!!!!!!FOUNTAIN!!!!!!!!!!!')
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
    hook.register('process_event', process_event)

    app.log.info('Succeful Rules Plugin registration', __name__)

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
