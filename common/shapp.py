#!/usr/local/bin/python3 -u
"""
    Author:     Oliver Ratzesberger <https://github.com/fxstein>
    Copyright:  Copyright (C) 2016 Oliver Ratzesberger
    License:    Apache License, Version 2.0
"""

# Make sure we have access to SentientHome commons
import os
import sys
import platform
import subprocess

try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
except:
    exit(1)

# Sentient Home Application
from common.shutil import boolify

import inspect
import configparser

# Storage engine support - might move into a plugin at some point in time
from influxdb import InfluxDBClient

from cement.core.foundation import CementApp
from cement.ext.ext_colorlog import ColorLogHandler
from cement.ext.ext_configparser import ConfigParserConfigHandler

LOG_FORMAT = '%(asctime)s (%(levelname)s) %(namespace)s: %(message)s'


class shLogHandler(ColorLogHandler):
    class Meta:
        file_format = LOG_FORMAT
        console_format = LOG_FORMAT
        debug_format = LOG_FORMAT


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
        config_files = ['~/.config/sentienthome/sentienthome.conf',
                        '/etc/sentienthome.conf']
        extensions = ['colorlog']
        arguments_override_config = True

# TODO: reload_config is currently not supported as of Cement 2.6 due to the
# fact that pyinotify does not support OSX. Opened an issue with Cement to see
# if the python watchdog extension could be used instead. Disabling for now to
# avoid erroring out due to missing package
#       extensions = ['reload_config', 'colorlog']

        log_handler = shLogHandler(colors=COLORS)
        config_handler = 'sh_config_handler'
        handlers = [shConfigHandler]

    def setup(self):
        # always run core setup first
        super(shApp, self).setup()

        # Interigate git for current version info
        self._initVersion()

        # Lets store who is using this module - used for filenames
        (self._origin_pathname, self._origin_filename) =\
            os.path.split(inspect.stack()[-1][1])

        self._retries = (int)(self.config.get('SentientHome',
                                              'retries',
                                              fallback=10))
        self._retry_interval = (float)(self.config.get('SentientHome',
                                                       'retry_interval',
                                                       fallback=2))

        self._checkpointing = boolify(self.config.get('SentientHome',
                                                      'checkpointing',
                                                      fallback='OFF'))

        # Setup event store and event engine configurations
        self._setEventStore()
        self._setEventEngine()
        self._setListener()

        # Once everything is setup log the application header
        self._LogHeader()

    def _initVersion(self, gitPath=None):
        """Initialize the version and GIT revision."""
        if not gitPath:
            gitPath = "git"
            self.log.debug("Git path not specified, using system path.")
        self._gitVersion = None
        self._gitRevision = None
        self._gitDirty = None
        try:
            self._gitVersion = subprocess.check_output(
                [gitPath, "--version"],
                stderr=subprocess.STDOUT).decode("utf-8").strip()
            self._gitRevision = subprocess.check_output(
                [gitPath, "describe", "--tags", "--always", "HEAD"],
                stderr=subprocess.STDOUT).decode("utf-8").strip()
            self._gitModifiedFiles = subprocess.check_output(
                [gitPath, "status", "--porcelain"],
                stderr=subprocess.STDOUT).decode("utf-8").splitlines()
            self._gitDirty = True if self._gitModifiedFiles else False
        except subprocess.CalledProcessError as e:
            self.log.debug(
                "Git information is not available: %s." %
                e.output.decode("utf-8"))
        except Exception as e:
            self.log.debug("Git is not available: %s" % e)

    def _LogHeader(self):
        """Log default logging header for App."""
        # Output default logheader
        self.log.info('#' * 78)
        self.log.info('#')
        self.log.info('# SentientHome')
        self.log.info('#')
        self.log.info('# Module:         %s' % self._origin_filename)
        self.log.info('# Path:           %s' % self._origin_pathname)
        self.log.info('# Revison:        %s' % self._gitRevision)
        self.log.info('# Dirty:          %s' % self._gitDirty)
        self.log.info('#')
        self.log.info('# Git:            %s' % self._gitVersion)
        self.log.info('#')
        self.log.info('# Python:         %s' % platform.python_version())
        # self.log.info('# Python Rev:     %s' % platform.python_revision())
        self.log.info('# Platform:       %s' % platform.platform())
        self.log.info('# Node:           %s' % platform.node())
        # self.log.info('# System:         %s' % platform.system())
        # self.log.info('# Release:        %s' % platform.release())
        # self.log.info('# Version:        %s' % platform.version())
        self.log.info('#')
        self.log.info('# Retries:        %s' % self._retries)
        self.log.info('# Interval:       %ss' % self._retry_interval)
        self.log.info('# Checkpointing:  %s' % self._checkpointing)
        self.log.info('#')
        self.log.info('# Event Store:    %s' % self._event_store)
        self.log.info('# Host:           %s' % self._event_store_host)
        self.log.info('# Port:           %s' % self._event_store_port)
        self.log.info('# User:           %s' % self._event_store_user)
        self.log.info('# Database:       %s' % self._event_store_db)
        self.log.info('# Info:           %s' % self._event_store_info)
        self.log.info('#')
        self.log.info('# Event Engine:   %s' % self._event_engine)
        self.log.info('# Host:           %s' % self._event_engine_addr)
        self.log.info('# Port:           %s' % self._event_engine_port)
        self.log.info('# Info:           %s' % self._event_engine_path_safe)
        self.log.info('#')
        self.log.info('# Event Listener: %s' % self._event_listener)
        self.log.info('# Host:           %s' % self._listener_path)
        self.log.info('#')
        self.log.info('#' * 78)

    def _setEventStore(self):
        config = self.config
        self._event_store = config.get('SentientHome', 'event_store',
                                       fallback='OFF')

        self._event_store_host = None
        self._event_store_port = None
        self._event_store_db = None
        self._event_store_user = None
        self._event_store_pass = None
        self._event_store_client = None
        self._event_store_info = None

        if self._event_store == 'OFF':
            self._event_store_active = 0
        elif self._event_store == 'INFLUXDB':
            self._event_store_active = 1
            self._event_store_host = config.get('influxdb', 'influx_host')
            self._event_store_port = config.get('influxdb', 'influx_port')
            self._event_store_db = config.get('influxdb', 'influx_db')
            self._event_store_user = config.get('influxdb', 'influx_user')
            self._event_store_pass = config.get('influxdb', 'influx_pass')

            try:
                self._event_store_client =\
                    InfluxDBClient(host=self._event_store_host,
                                   port=self._event_store_port,
                                   username=self._event_store_user,
                                   password=self._event_store_pass,
                                   database=self._event_store_db)
            except Exception as e:
                self.log.fatal(e)
                self.log.fatal('Exception creating InfluxDB client: %s' %
                               self._event_store_info)
                self._app.close(1)

            # safe event store path without password
            # can be used for reporting and general debugging
            self._event_store_info =\
                self._event_store_host + ':' + \
                self._event_store_port + ';db=' + \
                self._event_store_db + ';user=' + \
                self._event_store_user
        else:
            self.log.fatal('Unsupported event store: %s' % self._event_store)
            self.close(1)

        self.log.debug('Event store @: %s' % self._event_store_info)
        pass

    def _setEventEngine(self):
        config = self.config

        self._event_engine = config.get('SentientHome', 'event_engine',
                                        fallback='OFF')

        self._event_engine_active = 0

        self._event_engine_addr = None
        self._event_engine_port = None
        self._event_engine_path_safe = None
        self._event_engine_path = None

        if self._event_engine == 'ON':
            self._event_engine_active = 1
            self._event_engine_addr = config.get('SentientHome', 'event_addr')
            self._event_engine_port = config.get('SentientHome', 'event_port')
            self._event_engine_path_safe = \
                self._event_engine_addr + ':' + \
                self._event_engine_port + \
                config.get('SentientHome', 'event_path')

            # TODO: Add authentication to event engine
            self._event_engine_path = self._event_engine_path_safe

        self.log.debug('Event engine @: %s' % self._event_engine_path_safe)

    def _setListener(self):
        config = self.config

        self._event_listener = config.get('SentientHome', 'listener',
                                          fallback='OFF')
        self._listener_active = 0

        self._listener_path = None
        self._listener_auth = None

        if self._event_listener == 'ON':
            self._listener_active = 1
            self._listener_path = config.get('SentientHome', 'listener_addr')
            api_key = config.get('SentientHome', 'listener_api_key')

            self._listener_auth = {"Authorization": "token %s" % api_key}

        self.log.debug('Listener @: %s' % self._listener_path)

    @property
    def retries(self):
        return self._retries

    @property
    def retry_interval(self):
        return self._retry_interval

    @property
    def checkpointing(self):
        return self._checkpointing

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
