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
config.read(os.path.expanduser('~/.config/home/home.cfg'))

eagle_addr     = config.get('raineagle', 'eagle_addr')
eagle_poll_interval = int(config.get('raineagle', 'eagle_poll_interval', 1))
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

  idemanddata = raindata['InstantaneousDemand']

  imultiplier = int(idemanddata['Multiplier'], 16)
  idivisor = int(idemanddata['Divisor'], 16)
  idemand = int(idemanddata['Demand'], 16)

  if idemand > 0x7FFFFFFF: idemand -= 0x100000000
  if imultiplier == 0 : imultiplier = 1
  if idivisor == 0 : idivisor = 1

  power = ((idemand * imultiplier) / float (idivisor))*1000
  amps = power/240

  csumdata = raindata['CurrentSummation']

  csummultiplier = int(csumdata['Multiplier'], 16)
  csumdivisor = int(csumdata['Divisor'], 16)
  csumreceived = int(csumdata['SummationReceived'], 16)
  csumdelivered = int(csumdata['SummationDelivered'], 16)

  if csummultiplier == 0 : csummultiplier = 1
  if csumdivisor == 0 : csumdivisor = 1

  received = ((csumreceived * csummultiplier) / float (csumdivisor))*1000
  delivered = ((csumdelivered * csummultiplier) / float (csumdivisor))*1000

  event = [{
    'name': 'power',
    'columns': [ 'whole_house_power', 'whole_house_amps', 'whole_house_received', 'whole_house_delivered' ],
    'points': [[ power, amps, received, delivered ]]
  }]

  print event

  try:
    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
    print r
  except Exception:
    print 'Exception posting data to ' + influx_path
    pass

  time.sleep(eagle_poll_interval)
