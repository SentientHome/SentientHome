#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

from collections import defaultdict
import xml.etree.ElementTree as ET

def xml_to_dict(text):
    t = ET.fromstring(text)

    return etree_to_dict(t)

# Helper function needed to convert an XML response to a Dictionary
def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None }

    c = list(t)
    if c:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, c):
            for k, v in dc.iteritems():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if t.text:
        text = t.text.strip()
        if c or t.attrib:
            if text:
                d[t.tag] = numerify(text)
        else:
            # Turn numeric values into such
            d[t.tag] = numerify(text)
    return d

# Turn text encoded numeric values into numbers
def numerify(v):
    try:
      return int(v) if v.isdigit() else float(v)
    except ValueError:
      try:
        return v.encode('ascii')
      except ValueError:
        return v

# Conversion: Celcius to Fahrenheit
def CtoF(t):
  return (t*9)/5+32

# Conversion: mili Bar to inch Hg
def mBtoiHg(p):
  return p*0.02953

# Conversion: millimeter to inch
def mmtoin(m):
  return m*0.03937

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
