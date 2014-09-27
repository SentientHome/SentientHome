#!/usr/local/bin/python -u
__author__ = "Oliver Ratzesberger"

print "Starting InfluxDB JSON feed for Google Finance Stock Quotes"

import requests
import json
import random
import time
import os
import ConfigParser

# Turn text encoded numeric values into numbers - needed for InfluxDB
def numerify(v):
    try:
        return int(v) if v.isdigit() else float(v)
    except ValueError:
        return v.encode('ascii')

CODES_GOOGLE = {
  "c":      "change",
  "cp":     "price_close",
  "div":    "dividend",
  "e":      "exchange",
  "el":     "price_last_exchange",
  "elt":    "price_last_exchange_time",
  "l":      "price_last",
  "lt":     "price_last_datetime",
  "ltt":    "price_last_time",
  "lt_dts": "price_last_timestamp",
  "t":      "symbol",
  "id":     "id",
  "l_cur":  "l_cur",
  "ccol":   "ccol",
  "c_fix":  "c_fix",
  "l_fix":  "l_fix",
  "cp_fix": "cp_fix",
  "pcls_fix":"pcls_fix",
  "s":      "s",
}

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

stock_provider_addr   = config.get('stockquotes', 'stock_provider_addr')
stock_provider_port   = config.get('stockquotes', 'stock_provider_port')
stock_provider_path   = config.get('stockquotes', 'stock_provider_path')
stock_list            = config.get('stockquotes', 'stock_list')
stock_poll_interval   = int(config.get('stockquotes', 'stock_poll_interval', 1))
influx_addr           = config.get('influxdb', 'influx_addr')
influx_port           = config.get('influxdb', 'influx_port')
influx_db             = config.get('influxdb', 'influx_db')
influx_user           = config.get('influxdb', 'influx_user')
influx_pass           = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path
stock_path = "http://" + stock_provider_addr + ":" + stock_provider_port + stock_provider_path + stock_list
print "Stock Path: " + stock_path

while True:
  status = requests.get(stock_path)

  # Can't use raw JSON response from Google, must convert numbers to numeric
  quotes = [{k: numerify(v) for k, v in d.items()} for d in json.loads(status.text[3:])]

  # Have to iterate over quotes as some Google values seem optional depending on quote
  for quote in quotes:
    # Re-key the JSON response with friendly names
    rekeyed_quote = dict([(CODES_GOOGLE.get(key, key), value) for key, value in quote.iteritems()])

    event = [{
      'name': 'stockquotes',
      'columns': rekeyed_quote.keys(),
      'points': [ rekeyed_quote.values() ]
      }]

    print event

    try:
      r = requests.post(influx_path + "&p=" + influx_pass, data=json.dumps(event))
      print r
    except Exception:
      print 'Exception posting data to ' + influx_path
      pass

  time.sleep(stock_poll_interval)
