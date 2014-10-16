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

# Conversion: Celcius to Fahrenheit
def CtoF(t):
  return (t*9)/5+32

# Conversion: mili Bar to inch Hg
def mBtoiHg(p):
  return p*0.02953

# Conversion: millimeter to inch
def mmtoin(m):
  return m*0.03937

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
netatmo_unique        = int(config.get('netatmo', 'netatmo_unique', 1))
netatmo_poll_interval = int(config.get('netatmo', 'netatmo_poll_interval', 5))


influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

try:
  authorization = lnetatmo.ClientAuth( clientId = netatmo_client_id,
                            clientSecret = netatmo_client_secret,
                            username = netatmo_user,
                            password = netatmo_pass )
except Exception:
  # Something went wrong authorizing the connection to the NetAtmo service
  print "Error connecting to NetAtmo. Retrying in 60 sec..."

  time.sleep(60)
  try:
    print "Re-atempting NetAtmo Connection... "
    authorization = lnetatmo.ClientAuth( clientId = netatmo_client_id,
                              clientSecret = netatmo_client_secret,
                              username = netatmo_user,
                              password = netatmo_pass )
    pass
  except Exception:
    print "Repeat error connecting to Netatmo. Exiting..."
    raise

print "NetAtmo Connection established."

while True:
  devList = lnetatmo.DeviceList(authorization)

  # print devList.stations.keys()

  # Loop through all stations in the account
  for station in devList.stations.keys():

    station_name = devList.stations[station]['station_name']
    devData = devList.lastData(station=station_name)

    # Optional metric to imperal conversions
    # Not all sensors have all metrics
    for key in devData.keys():
      try:
        devData[key]['TemperatureF']=CtoF(devData[key]['Temperature'])
        devData[key]['min_tempF']=CtoF(devData[key]['min_temp'])
        devData[key]['max_tempF']=CtoF(devData[key]['max_temp'])
      except Exception:
        pass

      try:
        devData[key]['PressureiHg']=mBtoiHg(devData[key]['Pressure'])
      except Exception:
        pass

      try:
        devData[key]['sum_rain_1in']=mmtoin(devData[key]['sum_rain_1'])
        devData[key]['sum_rain_24in']=mmtoin(devData[key]['sum_rain_24'])
      except Exception:
        pass

      if netatmo_unique == 1:
        devData[key]['Module']=key
      else:
        devData[key]['Module']=station_name + '.' + key

      event = [{
        'name': 'netatmo',
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
