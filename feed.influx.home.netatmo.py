#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Netatmo"

import requests
import json
import random
import time
import os
import ConfigParser
import lnetatmo

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

influx_addr           = config.get('influxdb', 'influx_addr')
influx_port           = config.get('influxdb', 'influx_port')
influx_db             = config.get('influxdb', 'influx_db')
influx_user           = config.get('influxdb', 'influx_user')
influx_pass           = config.get('influxdb', 'influx_pass')
netatmo_client_id     = config.get('netatmo', 'netatmo_client_id')
netatmo_client_secret = config.get('netatmo', 'netatmo_client_secret')
netatmo_user          = config.get('netatmo', 'netatmo_user')
netatmo_pass          = config.get('netatmo', 'netatmo_pass')
netatmo_poll_interval = int(config.get('netatmo', 'netatmo_poll_interval', 5))


influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

authorization = lnetatmo.ClientAuth( clientId = netatmo_client_id,
                            clientSecret = netatmo_client_secret,
                            username = netatmo_user,
                            password = netatmo_pass )

while True:
  devList = lnetatmo.DeviceList(authorization)

  print devList.lastData().keys()

  devData = devList.lastData()

  for key in devData.keys():
    event = [{
      'name': 'netatmo.' + key,
      'columns': devData[key].keys(),
      'points': [ devData[key].values() ]
    }]

    print event

    try:
      r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
      print r
    except Exception:
      print 'Exception posting data to ' + influx_path
      pass

  time.sleep(netatmo_poll_interval)
