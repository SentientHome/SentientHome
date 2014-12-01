#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.abspath('..'))

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import etree_to_dict

import logging as log
log.info('Starting feed for Autelis PentAir Easytouch Controller')

import requests
import json
import xml.etree.ElementTree as ET
import time

config = shConfig('~/.config/home/home.cfg')

while True:
  response = requests.get('http://' + config.get('autelis', 'autelis_addr') +\
                        '/status.xml', auth=(config.get('autelis', 'autelis_user'),\
                         config.get('autelis', 'autelis_pass')))

  # For offline development:
  #data = etree_to_dict(ET.parse('samples/autelis.status.xml').getroot())

  data = etree_to_dict(ET.fromstring(response.text))
  # Data Structure Documentation: http://www.autelis.com/wiki/index.php?title=Pool_Control_(PI)_HTTP_Command_Reference

  alldata = dict(data['response']['equipment'].items() + \
                data['response']['system'].items() + \
                data['response']['temp'].items())

  event = [{
    'name': 'pool',
    'columns': alldata.keys(),
    'points': [ alldata.values() ]
  }]

  log.debug('Event data: %s', event)

  try:
    r = requests.post(config.getTargetPath(), data=json.dumps(event))
    log.info(r)
  except Exception:
    log.warn('Exception posting data to %s', config.getTargetPathSafe())
    pass

  time.sleep(config.getint('autelis', 'autelis_poll_interval', 5))
