#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for AUtelis PentAir Easytouch Controller"

import requests
import json
import random
import time
import os
import ConfigParser

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

autelis_addr     = config.get('autelis', 'autelis_addr')
influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path
 
while True:
  raindata= eg.get_device_data()

  idemand = raindata['InstantaneousDemand']

  multiplier = int(idemand['Multiplier'], 16)
  divisor = int(idemand['Divisor'], 16)
  demand = int(idemand['Demand'], 16)

  event = [{
    'name': 'pool',
    'columns': [ 'whole_house_power', 'whole_house_amps' ],
    'points': [[ power, amps ]]
  }]

  print event

  try:
    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
    print r
  except Exception:

    print 'Exception posting data to ' + influx_path
    pass

  time.sleep(5)
