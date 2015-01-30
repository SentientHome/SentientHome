#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))  + '/..')

# Sentient Home configuration
from common.shconfig import shConfig
from common.shutil import numerify
from common.sheventhandler import shEventHandler

import logging as log
log.info('Starting feed for Google Finance data')

import requests
import json

# Map more meaningful names to google finance codes
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

def quotes_feed(event_handler, finance_path, series_name, symbol_list):

    try:
        data = requests.get(finance_path + symbol_list)
    except Exception:
        log.warn('Exception getting data from %s%s', finance_path, symbol_list)
        return

    log.debug('Fetch data: %s', data.text)

    # Can't use raw JSON response from Google, must convert numbers to numeric
    financial_data = [{k: numerify(v) for k, v in d.items()}\
                        for d in json.loads(data.text[3:])]

    # Have to iterate over quotes as some Google values are optional
    for quote in financial_data:
        # Re-key the JSON response with friendly names
        rekeyed_quote = dict([(CODES_GOOGLE.get(key, key), value)\
                                for key, value in quote.iteritems()])

        event = [{
            'name': series_name,
            'columns': rekeyed_quote.keys(),
            'points': [ rekeyed_quote.values() ]
            }]

        log.debug('Event data: %s', event)

        event_handler.postEvent(event)


config = shConfig('~/.config/home/home.cfg')

finance_provider_addr = config.get('finance', 'finance_provider_addr')
finance_provider_port = config.get('finance', 'finance_provider_port')
finance_provider_path = config.get('finance', 'finance_provider_path')
finance_stock_list    = config.get('finance', 'finance_stock_list')
finance_index_list    = config.get('finance', 'finance_index_list')
finance_currency_list = config.get('finance', 'finance_currency_list')

finance_path = "http://" + finance_provider_addr + ":" + finance_provider_port + finance_provider_path
log.debug("Finance Path: %s", finance_path)

handler = shEventHandler(config, config.getfloat('finance', 'finance_poll_interval', 30))

while True:

  quotes_feed(handler, finance_path, 'indexes', finance_index_list)

  quotes_feed(handler, finance_path, 'stockquotes', finance_stock_list)

  quotes_feed(handler, finance_path, 'currencies', finance_currency_list)

  handler.sleep()
