#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Autelis PentAir Easytouch Controller"

import requests
import json
import xml.etree.ElementTree as ET
from   collections import defaultdict
import time
import os
import ConfigParser

# Helper function needed to convert part of the XML response to a Dictionary
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
            d[t.tag]['#text'] = text
      else:
        # When asigning the value try integer, then float, then text
        try:
          d[t.tag] = int(text)
        except ValueError:
          try:
            d[t.tag] = float(text)
          except ValueError:
            d[t.tag] = text
  return d

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

autelis_addr   = config.get('autelis', 'autelis_addr')
autelis_user   = config.get('autelis', 'autelis_user')
autelis_pass   = config.get('autelis', 'autelis_pass')
autelis_poll_interval = int(config.get('autelis', 'autelis_poll_interval', 1))
influx_addr    = config.get('influxdb', 'influx_addr')
influx_port    = config.get('influxdb', 'influx_port')
influx_db      = config.get('influxdb', 'influx_db')
influx_user    = config.get('influxdb', 'influx_user')
influx_pass    = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path

while True:
  status = requests.get('http://' + autelis_addr + '/status.xml', auth=(autelis_user, autelis_pass))

#  data = etree_to_dict(ET.parse('samples/autelis.status.xml').getroot())

  data = etree_to_dict(ET.fromstring(status.text))

  alldata = dict(data['response']['equipment'].items() + data['response']['system'].items() + data['response']['temp'].items())

  event = [{
    'name': 'pool',
    'columns': alldata.keys(),
    'points': [ alldata.values() ]
  }]

  print event

  try:
    r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
    print r
  except Exception:
    print 'Exception posting data to ' + influx_path
    pass

  time.sleep(autelis_poll_interval)
