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
      try:
        return v.encode('ascii')
      except ValueError:
        return v

def quotes_feed(influx_path, finance_path, series_name, symbol_list):

  print finance_path + symbol_list

  data = requests.get(finance_path + symbol_list)

  print data.text

  # Can't use raw JSON response from Google, must convert numbers to numeric
  financial_data = [{k: numerify(v) for k, v in d.items()} for d in json.loads(data.text[3:])]

  # Have to iterate over quotes as some Google values seem optional depending on quote
  for quote in financial_data:
    # Re-key the JSON response with friendly names
    rekeyed_quote = dict([(CODES_GOOGLE.get(key, key), value) for key, value in quote.iteritems()])

    event = [{
      'name': series_name,
      'columns': rekeyed_quote.keys(),
      'points': [ rekeyed_quote.values() ]
      }]

    print event

    try:
      r = requests.post(influx_path, data=json.dumps(event))
      print r
    except Exception:
      print 'Exception posting data to ' + influx_path[:influx_path.find('&p=')]
      pass


CODES_GOOGLE = {
  "c":      "change",
  "cp":     "change_pct",
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
  "pcls_fix":"price_prior_close",
  "s":      "s",
}

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/home.cfg'))

finance_provider_addr = config.get('finance', 'finance_provider_addr')
finance_provider_port = config.get('finance', 'finance_provider_port')
finance_provider_path = config.get('finance', 'finance_provider_path')
finance_stock_list    = config.get('finance', 'finance_stock_list')
finance_index_list    = config.get('finance', 'finance_index_list')
finance_currency_list = config.get('finance', 'finance_currency_list')
finance_poll_interval = int(config.get('finance', 'finance_poll_interval', 1))
influx_addr           = config.get('influxdb', 'influx_addr')
influx_port           = config.get('influxdb', 'influx_port')
influx_db             = config.get('influxdb', 'influx_db')
influx_user           = config.get('influxdb', 'influx_user')
influx_pass           = config.get('influxdb', 'influx_pass')

influx_path = "http://" + influx_addr + ":" + influx_port + "/db/" + influx_db + "/series?time_precision=s&u=" + influx_user
print "Path: " + influx_path
finance_path = "http://" + finance_provider_addr + ":" + finance_provider_port + finance_provider_path
print "Finance Path: " + finance_path

while True:

  quotes_feed(influx_path + "&p=" + influx_pass, finance_path, 'indexes', finance_index_list)

  quotes_feed(influx_path + "&p=" + influx_pass, finance_path, 'stockquotes', finance_stock_list)

  quotes_feed(influx_path + "&p=" + influx_pass, finance_path, 'currencies', finance_currency_list)

  time.sleep(finance_poll_interval)
