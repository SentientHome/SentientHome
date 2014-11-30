#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Universal Devices ISY994"

import requests
import json
import sys
import os
import ConfigParser

from  ISY.IsyEvent import ISYEvent

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.config/home/home.cfg'))
    
isy_addr = config.get('isy', 'isy_addr')
isy_user = config.get('isy', 'isy_user')
isy_pass = config.get('isy', 'isy_pass')
influx_addr = config.get('influxdb', 'influx_addr')
influx_port = config.get('influxdb', 'influx_port')
influx_db   = config.get('influxdb', 'influx_db')
influx_user = config.get('influxdb', 'influx_user')
influx_pass = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?u=" + influx_user
print "Path: " + influx_path

def event_feed(*arg):

  data = arg[0]

  event = [{
    'name': 'isy',
    'columns': data.keys(),
    'points': [ data.values() ]
  }]

  print event

  try:
    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
    print r
  except Exception:
    print 'Exception posting data to ' + influx_path
    pass


server = ISYEvent()
server.subscribe(addr=isy_addr, userl=isy_user, userp=isy_pass)
server.set_process_func(event_feed, "")

try:
  print "Use Control-C to exit"
  server.events_loop()   #no return
except KeyboardInterrupt:
  print "Exiting"
