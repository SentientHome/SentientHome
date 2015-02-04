#!/usr/local/bin/python3 -u
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
    d = {t.tag: {} if t.attrib else None}

    c = list(t)
    if c:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, c):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
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
    except Exception:
        return v

# Helper to rekey flattened dicts in dot notation
def rekey_dict(key, d):
    return dict((key + '.' + k, numerify(v)) for k, v in d.items())

# Helper to flatten embeded structures
# If there is a dict within a dict this function will pop the dict and
# insert is rekeyed keys and values into the main dict. The key of the
# embedded dict will be prepended with a separator '.' to the keys
def flatten_dict(d):
    f = d

    if type(d) is dict:
        # Interate over keys to check for embeded dicts
        keys = d.keys()
        for k in keys:
            if type(d[k]) is dict:
                subdict = d.pop(k)
                # Rekey the sub dict in dot notation
                r = rekey_dict(k, subdict)
                # Recursion to walk embeded structures
                r2 = flatten_dict(r)
                f = dict(d.items() + r2.items())

    return f

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
