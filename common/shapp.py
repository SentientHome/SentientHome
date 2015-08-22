#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import os
import inspect
import configparser

from cement.core.foundation import CementApp
from cement.core import handler
from cement.core.interface import Interface, Attribute
from cement.ext.ext_colorlog import ColorLogHandler
from cement.ext.ext_configparser import ConfigParserConfigHandler

class shConfigHandler(ConfigParserConfigHandler):
    class Meta:
        label = 'sh_config_handler'

    def get(self, *args, **kw):
        try:
            return super(shConfigHandler, self).get(*args, **kw)
        except configparser.Error as e:
            self.app.log.fatal('Missing configuration setting: %s' % e)
            self.app.close(1)

COLORS = {
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'white,bg_red',
}

class shApp(CementApp):
    class Meta:
        config_files = ['~/.config/sentienthome/sentienthome.conf']
        extensions = ['colorlog']
        arguments_override_config = True

# TODO: reload_config is currently not supported as of Cement 2.6 due to the
# fact that pyinotify does not support OSX. Opened an issue with Cement to see
# if the python watchdog extension could be used instead. Disabling for now to
# avoid erroring out due to missing package
#       extensions = ['reload_config', 'colorlog']

        log_handler = ColorLogHandler(colors=COLORS)
        config_handler = 'sh_config_handler'
        handlers = [shConfigHandler]

    def setup(self):
        # always run core setup first
        super(shApp, self).setup()

        # Lets store who is using this module - used for filenames
        (self._origin_pathname, self._origin_filename) = os.path.split(inspect.stack()[-1][1])

        self._retries = (int)(self.config.get('SentientHome', 'retries', fallback=10))
        self._retry_intervall = (float)(self.config.get('SentientHome',\
                                                     'retry_interval',\
                                                      fallback=2))

        # Setup event store and event engine configurations
        self._setEventStore()
        self._setEventEngine()


    def _setEventStore(self):
        config = self.config
        self._event_store     = config.get('SentientHome', 'event_store',\
                                            fallback='OFF')

        self._event_store_addr      = None
        self._event_store_port      = None
        self._event_store_db        = None
        self._event_store_user      = None
        self._event_store_pass      = None
        self._event_store_path_safe = None
        self._event_store_path      = None

        if self._event_store=='OFF':
            self._event_store_active    = 0
        elif self._event_store=='INFLUXDB':
            self._event_store_active    = 1
            self._event_store_addr      = config.get('influxdb', 'influx_addr')
            self._event_store_port      = config.get('influxdb', 'influx_port')
            self._event_store_db        = config.get('influxdb', 'influx_db')
            self._event_store_user      = config.get('influxdb', 'influx_user')
            self._event_store_pass      = config.get('influxdb', 'influx_pass')

            # safe event store path without password
            # can be used for reporting and general debugging
            self._event_store_path_safe =\
                        self._event_store_addr + ':' + \
                        self._event_store_port + '/db/' + \
                        self._event_store_db + '/series?time_precision=s&u=' + \
                        self._event_store_user
            # complete event store path with full authentication
            self._event_store_path = self._event_store_path_safe +\
                                '&p=' + self._event_store_pass
        else:
            self.log.fatal('Unsupported event store: %s' % self._event_store)
            self.close(1)

        self.log.debug('Event store @: %s' % self._event_store_path_safe)
        pass

    def _setEventEngine(self):
        config = self.config

        self._event_engine_addr         = None
        self._event_engine_port         = None
        self._event_engine_path_safe    = None
        self._event_engine_path         = None

        if config.get('SentientHome', 'event_engine', fallback='OFF' ) == 'ON':
            self._event_engine_active = 1
            self._event_engine_addr   = config.get('SentientHome', 'event_addr')
            self._event_engine_port   = config.get('SentientHome', 'event_port')
            self._event_engine_path_safe = \
                            self._event_engine_addr + ':' + \
                            self._event_engine_port + \
                            config.get('SentientHome', 'event_path')

            # TODO: Add authentication to event engine
            self._event_engine_path = self._event_engine_path_safe
        else:
            self._event_engine_active = 0

        self.log.debug('Event engine @: %s' % self._event_engine_path_safe)

    @property
    def retries(self):
        return self._retries

    @property
    def event_store(self):
        return self._event_store

    @property
    def event_store_active(self):
        return self._event_store_active

    @property
    def event_store_path_safe(self):
        return self._event_store_path_safe

    @property
    def event_store_path(self):
        return self._event_store_path

    @property
    def event_engine_active(self):
        return self._event_engine_active

    @property
    def event_engine_path_safe(self):
        return self._event_engine_path_safe

    @property
    def event_engine_path(self):
        return self._event_engine_path

    @property
    def origin_filename(self):
        return self._origin_filename

    @property
    def origin_pathname(self):
        return self._origin_pathname

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
