#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from cement.core import hook
from cement.utils.misc import init_defaults

sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                '/../dependencies/ISYlib-python')

from ISY.IsyClass import Isy

defaults = init_defaults('plugin.isy')


def extend_isy_object(app):

    isy_addr = app.config.get('isy', 'isy_addr')
    isy_user = app.config.get('isy', 'isy_user')
    isy_pass = app.config.get('isy', 'isy_pass')

    app.log.debug('Connecting to ISY controller @%s' % isy_addr)

    try:
        isy = Isy(addr=isy_addr, userl=isy_user, userp=isy_pass)
    except Exception as e:
        app.log.error('Unable to connect to ISY controller @%s' % isy_addr)
        app.log.error(e)
        return

    # extend the event engine app object with an ``isy`` member
    app.extend('isy', isy)

    app.log.info('Succeful ISY Plugin registration')


def load(app):
    hook.register('post_run', extend_isy_object)


#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
