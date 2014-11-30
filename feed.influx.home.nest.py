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
config.read(os.path.expanduser('~/.config/home/home.cfg'))

influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')
nest_user      = config.get('nest', 'nest_user')
nest_pass      = config.get('nest', 'nest_pass')
nest_cache     = config.get('nest', 'nest_cache')
nest_poll_interval = int(config.get('nest', 'nest_poll_interval', 60))

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

nest = nest_thermostat.Nest(nest_user, nest_pass, access_token_cache_file=os.path.expanduser(nest_cache))

structures = nest.structures

for structure in structures:
  print '==========================='
  print 'Structure: ' + structure.name
  print 'Away     : ' + str(structure.away)
#  print 'Location : ' + structure.location
#  print 'Address  : ' + structure.address
  print 'ZIP      : ' + structure.postal_code

devices = nest.devices

for device in devices:
  print '---------------------------'
  print 'Device   : ' + device.name
  print 'Serial   : ' + device._serial
  print 'Temp     : ' + str(device.temperature)
  print 'Humidity : ' + str(device.humidity)
  print 'Fan      : ' + str(device.fan)
  print 'Mode     : ' + device.mode
  print 'Target   : ' + str(device.target)
  print 'ZIP      : ' + device.postal_code


for key in nest._status.keys():
  print '============================'
  print 'Key    : ' + key
  print 'Subkeys: ' + str(nest._status[key].keys())

  for subkey in nest._status[key].keys():
    print '----------------------------'
    print 'SubKey  : ' + subkey + ' = ' + str(nest._status[key][subkey])
    print 'Sub2keys: ' + str(nest._status[key][subkey].keys())

    for sub2key in nest._status[key][subkey].keys():
      print '++++++++++++++++++++++++++++'
      print 'Sub2Key  : ' + sub2key + ' = ' + str(nest._status[key][subkey][sub2key])
      try:
        print 'Sub3keys: ' + str(nest._status[key][subkey][sub2key].keys())
      except Exception:
        continue


while True:


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
