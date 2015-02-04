#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import os
import time
from configparser import ConfigParser
import logging as log

log.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')

class shConfig:
    'SentientHome minimalistic configuration automation'

    def __init__(self, config_path):
        self._config = ConfigParser()
        self._config_path = os.path.expanduser(config_path)

        self._logger = log.getLogger()

        self._readConfig()


    def _readConfig(self):
        try:
            log.info('Reading SentientHome configuration from: %s', self._config_path)
            self._config.read(self._config_path)
        except Exception:
            log.critical('Unable to read configuration from: %s', self._config_path)
            raise

        self._config_modified = os.path.getmtime(self._config_path)

        self._loglevel = self.get('sentienthome', 'loglevel', 'DEFAULT')
        self._retries = self.getint('sentienthome', 'retries', 10)

        log.info('Switching logging to %s level.', self._loglevel)

        if self._loglevel == 'INFO':
            self._logger.setLevel(log.INFO)
        elif self._loglevel == 'DEBUG':
            self._logger.setLevel(log.DEBUG)
        elif self._loglevel == 'WARNING':
            self._logger.setLevel(log.WARNING)
        elif self._loglevel == 'ERROR':
            self._logger.setLevel(log.ERROR)
        elif self._loglevel == 'CRITICAL':
            self._logger.setLevel(log.CRITICAL)
        elif self._loglevel == 'DEFAULT':
            log.info('Logging at system default level.')
        else:
            log.warn('SentientHome: Unsupported logging level')

        self._setEventStore()

        self._setEventEngine()

        # Record time stamp of latest config update
        self._config_last_time = time.time()


    def reloadModifiedConfig(self):
        # Limit reload to once ever 10s+
        if (time.time() - self._config_last_time) > 10:
            # test if configfile has been updated and if so reload
            if self._config_modified != os.path.getmtime(self._config_path):
                log.info('Config file modification detected. Reloading %s', self._config_path)
                self._readConfig()


    def get(self, section, setting, default=''):
        try:
            return self._config.get(section, setting)
        except Exception:
            if default:
                return default
            else:
                raise

    def getint(self, section, setting, default=''):
        try:
            return self._config.getint(section, setting)
        except Exception:
            if default != '':
                return default
            else:
                raise

    def getfloat(self, section, setting, default=''):
        try:
            return self._config.getfloat(section, setting)
        except Exception:
            if default != '':
                return default
            else:
                raise

    def _setEventStore(self):
        self._event_store     = self.get('sentienthome', 'event_store', 'INFLUXDB')

        if self._event_store=='DEVNULL':
            self._event_store_active = 0
            self._event_store_addr   = None
            self._event_store_port   = None
            self._event_store_db     = None
            self._event_store_user   = None
            self._event_store_pass   = None
            self._event_store_path_safe = None
            self._event_store_path   = None
        elif self._event_store=='INFLUXDB':
            self._event_store_active = 1
            self._event_store_addr   = self.get('influxdb', 'influx_addr')
            self._event_store_port   = self.get('influxdb', 'influx_port')
            self._event_store_db     = self.get('influxdb', 'influx_db')
            self._event_store_user   = self.get('influxdb', 'influx_user')
            self._event_store_pass   = self.get('influxdb', 'influx_pass')

            # safe event store path without password
            # can be used for reporting and general debugging
            self._event_store_path_safe =\
                    "http://" + self._event_store_addr + ":" + \
                                self._event_store_port + "/db/" + \
                                self._event_store_db + "/series?time_precision=s&u=" + \
                                self._event_store_user
            # complete event store path with full authentication
            self._event_store_path = self._event_store_path_safe +\
                                "&p=" + self._event_store_pass
        else:
            log.critical('Unsupported event store: %s', self._event_store)

        log.debug('Event store @: %s', self._event_store_path_safe)

    def _setEventEngine(self):
        self._event_engine_active = self.getint('sentienthome', 'event_engine', 0)

        # TODO: Implement event engine
        self._event_engine_path = None
        self._event_engine_path_safe = None

        if self._event_engine_active == 1:
            log.debug('Event engine @: %s', self._event_engine_path_safe)

    @property
    def config(self):
        return self._config

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

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
