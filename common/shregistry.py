#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# ALL event types need to be registered here
# ATTENTION: type must be unique to avoid event name space polution

# Registry structure:
# key   = unique identifier of event type
# name  = unique namespace of event should be same as key in most cases
# class = class of events for grouping and statistics
# desc  = description of event types
# tags  = list of freeform tags
#
# Notes:
# keys and types should be kept short and shpuld be kept constant for the life
# of the project

shRegistry = {
    'apcups'   : {'name': 'apcups',   'class': 'Power',      'desc': 'APC UPS', 'tags': ['APC', 'Schneider Electric', 'UPS']},
    'autelis'  : {'name': 'autelis',  'class': 'Pool',       'desc': 'Autelis Pool Controller', 'tags': ['Pool', 'Autelis', 'Pentair']},
    'eagle'    : {'name': 'eagle',    'class': 'Power',      'desc': 'Rainforest Eagle Gateway', 'tags':['Rainforest', 'Eagle', 'Power', 'Electricity']},
    'gfinance' : {'name': 'gfinance', 'class': 'Finance',    'desc': 'Google Finance', 'tags': ['Google', 'Finance', 'Stock', 'Currency', 'Index']},
    'isy'      : {'name': 'isy',      'class': 'Automation', 'desc': 'ISY994 Home Automation Controller', 'tags':['ISY', 'Insteon', 'X10']},
    'nesttherm': {'name': 'nesttherm','class': 'Climate',    'desc': 'Nest Thermostat', 'tags':['Nest', 'Thermostat']},
    'nestfire' : {'name': 'nestfire', 'class': 'Protection', 'desc': 'Nest Fire & CO Alarm', 'tags':['Nest', 'Protect', 'Fire Alarm', 'CO Alarm']},
    'netatmo'  : {'name': 'netatmo',  'class': 'Climate',    'desc': 'Netatmo Climate Station', 'tags':['Climate', 'Indoor', 'Outdoor']},
    'smawebbox': {'name': 'smawebbox','class': 'Power',      'desc': 'SMA Sunny Webbox', 'tags':['SMA', 'Sunny', 'Webbox', 'Power', 'Electricity', 'Solar']},
    'twitter'  : {'name': 'twitter',  'class': 'Social',     'desc': 'Twitter Feed', 'tags':['Twitter', 'Social', 'Tweet']},
    'ubnt.mfi' : {'name': 'ubnt.mfi', 'class': 'Automation', 'desc': 'Ubiquiti mFi', 'tags':['Ubiquiti', 'ubnt', 'Unifi', 'mFi']},
    'usgsquake': {'name': 'usgsquake','class': 'Geological', 'desc': 'USGS Earthquakes', 'tags':['USGS', 'Earthquake']},
    'zillow'   : {'name': 'zillow',   'class': 'Finance',    'desc': 'Zillow Home Valuation', 'tags':['Zillow', 'House', 'Home', 'Value', 'Fiance']},

    # Sentient Home Internal Event Types
    'tracer'   : {'name': 'tracer',   'class': 'Internal',   'name': 'Sentient Home Periodic Tracer', 'tags': ['Sentient Home', 'Tracer']},
    'loadtest' : {'name': 'loadtest', 'class': 'Internal',   'name': 'Sentient Home Load Test Event Generator', 'tags': ['Sentient Home', 'Test']},
}

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)

    print("syntax ok")

    exit(0)
