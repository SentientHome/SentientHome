#!/usr/local/bin/python3 -u
"""
    Author:     Oliver Ratzesberger <https://github.com/fxstein>
    Copyright:  Copyright (C) 2016 Oliver Ratzesberger
    License:    Apache License, Version 2.0
"""

from collections import defaultdict
import xml.etree.ElementTree as ET
import locale
import time


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
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
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
# Added locale functions to deal with thousands separators in incoming
def numerify(v):
    try:
        return float(v)
    except Exception:
        try:
            return locale.atof(v)
        except Exception:
            return v


# Helper to rekey flattened dicts in dot notation
def rekey_dict(key, d):
    return dict((key + '.' + k, numerify(v)) for k, v in d.items())


# Helper to flatten embeded structures
# If there is a dict within a dict this function will pop the dict and
# insert it's rekeyed keys and values into the main dict. The key of the
# embedded dict will be prepended with a separator '.' to the keys
def flatten_dict(d):
    f = d

    if type(d) is dict:
        # Interate over keys to check for embeded dicts
        keys = list(d.keys())
        for k in keys:
            if type(d[k]) is dict:
                subdict = d.pop(k)
                # Rekey the sub dict in dot notation
                r = rekey_dict(k, subdict)
                # Recursion to walk embeded structures
                r2 = flatten_dict(r)
                f = dict(list(d.items()) + list(r2.items()))

    return f


# Helper function to extract tags out of data dict
def extract_tags(data, keys):
    tags = dict()

    for key in keys:
        try:
            tags[key] = data.pop(key)
        except KeyError:
            # Skip optional tags
            pass

    return tags


# Conversion: Celcius to Fahrenheit
def CtoF(t):
    return (t*9)/5+32


# Conversion: mili Bar to inch Hg
def mBtoiHg(p):
    return p*0.02953


# Conversion: millimeter to inch
def mmtoin(m):
    return m*0.03937


# Conversion: square meter to square foot
def m2toft2(a):
    return a*10.764


# Conversion: string to bool
def boolify(s):
    return (str)(s).lower() in['true', '1', 't', 'y', 'yes', 'on', 'enable',
                               'enabled']


# Conversion: string to bool to int
def boolify2int(str):
    return (int)(boolify(str))


# Conversion epoch to local timestamp string
def epoch2date(epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
