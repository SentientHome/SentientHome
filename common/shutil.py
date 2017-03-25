#!/usr/local/bin/python3 -u
"""
SentientHome utility functions.

Author:     Oliver Ratzesberger <https://github.com/fxstein>
Copyright:  Copyright (C) 2017 Oliver Ratzesberger
License:    Apache License, Version 2.0
"""

from collections import defaultdict
import locale
import time
import xml.etree.ElementTree as ET


def xml_to_dict(text):
    """Parse an xml document into a python dict."""
    t = ET.fromstring(text)

    return etree_to_dict(t)


def etree_to_dict(t):
    """Helper function needed to convert an XML response to a dict."""
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


def numerify(v):
    """Turn text encoded numeric values into numbers.

    Added locale functions to deal with thousands separators in incoming
    """
    try:
        return float(v)
    except Exception:
        try:
            return locale.atof(v)
        except Exception:
            return v


def rekey_dict(key, d):
    """Helper to rekey flattened dicts in dot notation."""
    return dict((key + '.' + k, numerify(v)) for k, v in d.items())


def flatten_dict(d):
    """Helper to flatten embeded structures.

    If there is a dict within a dict this function will pop the dict and
    insert it's rekeyed keys and values into the main dict. The key of the
    embedded dict will be prepended with a separator '.' to the keys
    """
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


def extract_tags(data, keys):
    """Helper function to extract tags out of data dict."""
    tags = dict()

    for key in keys:
        try:
            tags[key] = data.pop(key)
        except KeyError:
            # Skip optional tags
            pass

    return tags


def CtoF(t):
    """Conversion: Celcius to Fahrenheit."""
    return (t*9)/5+32


def mBtoiHg(p):
    """Conversion: mili Bar to inch Hg."""
    return p*0.02953


def mmtoin(m):
    """Conversion: millimeter to inch."""
    return m*0.03937


def m2toft2(a):
    """Conversion: square meter to square foot."""
    return a*10.764


def boolify(s):
    """Conversion: string to bool."""
    return (str)(s).lower() in['true', '1', 't', 'y', 'yes', 'on', 'enable',
                               'enabled']


def boolify2int(str):
    """Conversion: string to bool to int."""
    return (int)(boolify(str))


def epoch2date(epoch):
    """# Conversion epoch to local timestamp string."""
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
