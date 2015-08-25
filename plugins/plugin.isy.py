#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from cement.core import handler, hook
from cement.core.controller import CementBaseController
from cement.utils.misc import init_defaults

sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                '/../dependencies/ISYlib-python')

from ISY.IsyClass import Isy

defaults = init_defaults('plugin.isy')


class ISYPluginController(CementBaseController):
    class Meta:
        label = 'plugin.isy'
        description = 'this is my plugin description'
        stacked_on = 'base'
        config_defaults = defaults


def isy_hook(app):
    # do something magical
    print('Something Magical is Happening!')


def load(app):
    handler.register(ISYPluginController)
    hook.register('post_run', isy_hook)
