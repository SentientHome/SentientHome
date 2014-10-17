#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Nest"

import requests
import json
import random
import time
import os
import ConfigParser
#from sanction import Client
import nest_thermostat

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')
nest_client_id         = config.get('nest', 'nest_client_id')
nest_client_secret     = config.get('nest', 'nest_client_secret')
nest_client_pin        = config.get('nest', 'nest_client_pin')
nest_poll_interval     = int(config.get('nest', 'nest_poll_interval', 60))

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

#c = Client(token_endpoint="https://api.home.nest.com/oauth2/access_token",
#    client_id = nest_client_id,
#    client_secret = nest_client_secret)

#c.request_token(code = nest_client_pin)

nest = nest_thermostat.Nest(USERNAME, PASSWORD)

structures = nest.structures

while True:
#  data = c.request('wss://developer-api.nest.com')

#  print data

  event = [{
    'name': 'nest',
    'columns': [ 'XXXX', 'YYYY' ],
    'points': [[ 1, 2 ]]
  }]

  print event

#  try:
#    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
#    print r
#  except Exception:
#    print 'Exception posting data to ' + influx_path
#    pass

  time.sleep(nest_poll_interval)
