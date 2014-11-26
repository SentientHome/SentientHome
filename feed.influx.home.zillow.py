#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Zillow Home Data"

import requests
import json
import xml.etree.ElementTree as ET
from   collections import defaultdict
import time
import os
import locale
import ConfigParser

# Helper function needed to convert part of the XML response to a Dictionary
# Enhanced version to convert numeric data from strings to numeric data types
# leverage locale.atoi and atof to deal with thousand separators
def etree_to_dict(t):
  d = {t.tag: {} if t.attrib else None }

  children = list(t)
  if children:
      dd = defaultdict(list)
      for dc in map(etree_to_dict, children):
          for k, v in dc.iteritems():
              dd[k].append(v)
      d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
  if t.attrib:
      d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
  if t.text:
      text = t.text.strip()
      if children or t.attrib:
          if text:
            # When asigning the value try integer, then float, then text
            try:
              d[t.tag] = locale.atoi(text)
            except ValueError:
              try:
                d[t.tag] = locale.atof(text)
              except ValueError:
                d[t.tag]['text'] = text
      else:
        # When asigning the value try integer, then float, then text
        try:
          d[t.tag] = locale.atoi(text)
        except ValueError:
          try:
            d[t.tag] = locale.atof(text)
          except ValueError:
            d[t.tag] = text
  return d

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.config/home/home.cfg'))

zillow_addr            = config.get('zillow', 'zillow_addr')
zillow_port            = config.get('zillow', 'zillow_port')
zillow_path            = config.get('zillow', 'zillow_path')
zillow_zws_id          = config.get('zillow', 'zillow_zws_id')
zillow_zpid            = config.get('zillow', 'zillow_zpid')
zillow_poll_interval  = int(config.get('zillow', 'zillow_poll_interval', 3600))
influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

zillow_request = 'http://' + zillow_addr + ":" + zillow_port + zillow_path + "?zws-id=" + zillow_zws_id + "&zpid=" + zillow_zpid
print "Zillow Request: " + zillow_request

while True:
  status = requests.get(zillow_request)

  #print status.text

  # set locale so we can easily strip the komma in the zindexValue
  locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' )
  data = etree_to_dict(ET.fromstring(status.text))
  # Data Structure Documentation: http://www.zillow.com/howto/api/APIOverview.htm

  property_data = data['{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate']['response']['zestimate']
  local_data = data['{http://www.zillow.com/static/xsd/Zestimate.xsd}zestimate']['response']['localRealEstate']

  event = [{
    'name': 'zillow',
    'columns': ['valuation', '30daychange', 'rangehigh', 'rangelow', 'percentile', 'last-updated',
                'region', 'regiontype', 'zindexValue'],
    'points': [[ property_data['amount'], property_data['valueChange'],
                property_data['valuationRange']['high'],
                property_data['valuationRange']['low'],
                property_data['percentile'],
                property_data['last-updated'],
                local_data['region']['@name'],
                local_data['region']['@type'],
                local_data['region']['zindexValue']
                ]]
  }]

  print event

  try:
    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
    print r
  except Exception:
    print 'Exception posting data to ' + influx_path
    pass

  time.sleep(zillow_poll_interval)
