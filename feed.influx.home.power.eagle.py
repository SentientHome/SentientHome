#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Rainforest Eagle"

import requests
import json
import random
import time
import os
import ConfigParser

from RainEagle import Eagle, to_epoch_1970

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

eagle_addr     = config.get('raineagle', 'eagle_addr')
influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path
 
eg = Eagle(debug=0, addr=eagle_addr)

while True:
  raindata= eg.get_device_data()

  idemand = raindata['InstantaneousDemand']

  multiplier = int(idemand['Multiplier'], 16)
  divisor = int(idemand['Divisor'], 16)
  demand = int(idemand['Demand'], 16)

  if demand > 0x7FFFFFFF: demand -= 0x100000000

  if multiplier == 0 : multiplier = 1

  if divisor == 0 : divisor = 1

  power = ((demand * multiplier) / float (divisor))*1000
  amps = power/240

  event = [{
    'name': 'power',
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
