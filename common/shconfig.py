#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

import os
import ConfigParser
import logging as log

log.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s')

class shConfig:
    'SentientHome minimalistic configuration automation'

    def __init__(self, configPath):
        self._config = ConfigParser.SafeConfigParser()

        try:
            log.info('Reading Sentient Home configuration from: %s', configPath)
            self._config.read(os.path.expanduser(configPath))
        except Exception:
            try:
                self._config.read(configPath)
            except Exception:
                raise

        self._loglevel = self.get('sentienthome', 'loglevel', 'DEFAULT')
        self._logger = log.getLogger()

        if self._loglevel == 'INFO':
            self._logger.setLevel(log.INFO)
            log.info('Switching logging to INFO level.')
        elif self._loglevel == 'WARN':
            self._logger.setLevel(log.WARN)
            log.warn('Switching logging to WARN level.')
        elif self._loglevel == 'DEBUG':
            self._logger.setLevel(log.DEBUG)
            log.debug('Switching logging to DEBUG level.')
        elif self._loglevel == 'DEFAULT':
            log.info('Logging at system default level.')
        else:
            log.warn('SentientHome: Unsupported logging level')

        self._setTarget()

        self._setRulesEngine()

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

    def _setTarget(self):
        self._target         = self.get('sentienthome', 'target', 'INFLUXDB')

        if self._target=='INFLUXDB':
            self._target_addr = self.get('influxdb', 'influx_addr')
            self._target_port = self.get('influxdb', 'influx_port')
            self._target_db   = self.get('influxdb', 'influx_db')
            self._target_user = self.get('influxdb', 'influx_user')
            self._target_pass = self.get('influxdb', 'influx_pass')

            # safe path without password
            self._target_path_safe = "http://" + self._target_addr + ":" + \
                                self._target_port + "/db/" + \
                                self._target_db + "/series?time_precision=s&u=" + \
                                self._target_user
            # complete target path with full authentication
            self._target_path = self._target_path_safe + "&p=" + self._target_pass
        else:
            log.critical('Unsupported target output: %s', self._target)

        log.debug('Target output: %s', self._target_path_safe)

    def _setRulesEngine(self):
        self._rules_engine_active = self.getint('sentienthome', 'rules_engine', 0)

        # TODO: Implement rules engine
        self._rules_path = None
        self._rules_path_safe = None

        if self._rules_engine_active == 1:
            log.debug('Rules engine at: %s', self._target_path_safe)

    @property
    def config(self):
        return self._config

    @property
    def target(self):
        return self._target

    @property
    def target_path_safe(self):
        return self._target_path_safe

    @property
    def target_path(self):
        return self._target_path

    @property
    def rules_engine_active(self):
        return self._rules_engine_active

    @property
    def rules_path_safe(self):
        return self._rules_path_safe

    @property
    def rules_path(self):
        return self._rules_path

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
