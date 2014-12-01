#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2014 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

from collections import defaultdict

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

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
