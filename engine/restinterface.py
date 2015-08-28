#!/usr/local/bin/python3 -u
__author__ = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__ = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

import asyncio
from aiohttp import web
import json
import time
from collections import defaultdict


class shRestInterface:
    'SentientHome event engine restful interfaces'

    def __init__(self, app):
        self._app = app
        self._webapp = app._webapp
        self._memory = app._memory

        self._webapp.router.add_route('GET', '/', self.handle_default)
        self._webapp.router.add_route('GET', '/cacheinfo',
                                      self.handle_cacheinfo)
        self._webapp.router.add_route('GET', '/cache/{name}',
                                      self.handle_samplecache)
        self._webapp.router.add_route('GET', '/cache/isy/control/{name}',
                                      self.handle_isycontrol)
        self._webapp.router.add_route('GET', '/cache/isy/controlinfo',
                                      self.handle_isycontrolinfo)
        self._webapp.router.add_route('GET', '/cache/isy/state/{node}',
                                      self.handle_isystate)

    @asyncio.coroutine
    def handle_default(self, request):
        output = {'msg': 'SentientHome Event Engine',
                  'body': 'I`m alive!'}

        self._app.log.debug('Response: %s' % output)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

    @asyncio.coroutine
    def handle_samplecache(self, request):

        try:
            name = request.match_info.get('name', 'all')

            output = {'msg': 'SentientHome Event Engine',
                      'body': name + ' Sample Data',
                      'events': []}

            for i in range(0, 50):
                try:
                    output['events'].append(self._memory.eventmemory['raw'][
                        name][i])
                except Exception:
                    break
        except Exception as e:
            self._app.log.error('Exception: %s' % e)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

    @asyncio.coroutine
    def handle_cacheinfo(self, request):
        try:
            output = {'msg': 'SentientHome Event Engine',
                      'body': 'Cache Statistics',
                      'cacheinfo': []}

            for c in self._memory.eventmemory:
                cacheinfo = dict()
                cacheinfo[c + '.maxlen'] = self._memory.eventmemory['raw'][
                    c].maxlen
                cacheinfo[c + '.len'] = len(self._memory.eventmemory['raw'][c])

                # Calculate event statistics
                eventcount = 0
                timenow = time.time() * 1000
                events1sec = 0
                events10sec = 0
                events1min = 0
                events10min = 0
                events1h = 0
                for e in self._memory.eventmemory['raw'][c]:
                    eventcount = eventcount + 1
                    tdelta = timenow - e['shtime2']
                    if tdelta <= 1000:
                        events1sec = eventcount
                    if tdelta <= 10000:
                        events10sec = eventcount
                    if tdelta <= 60000:
                        events1min = eventcount
                    if tdelta <= 600000:
                        events10min = eventcount
                    if tdelta <= 3600000:
                        events1h = eventcount
                    else:
                        break

                cacheinfo[c + '.events1sec'] = events1sec
                cacheinfo[c + '.events10sec'] = events10sec
                cacheinfo[c + '.events10secrate'] = events10sec/10
                cacheinfo[c + '.events1min'] = events1min
                cacheinfo[c + '.events1minrate'] = events1min/60
                cacheinfo[c + '.events10min'] = events10min
                cacheinfo[c + '.events10minrate'] = events10min/600
                cacheinfo[c + '.events1h'] = events1h
                cacheinfo[c + '.events1hrate'] = events1h/3600

                output['cacheinfo'].append(cacheinfo)
        except Exception as e:
            self._app.log.error('Exception: %s' % e)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

    @asyncio.coroutine
    def handle_isycontrol(self, request):

        try:
            name = request.match_info.get('name', 'ST')

            output = {'msg': 'SentientHome Event Engine',
                      'body': 'isy/' + name + ' Sample Data',
                      'events': []}

            i = 0
            for e in self._memory.eventmemory['raw']['isy']:
                try:
                    if e['Event.control'] == name:
                        output['events'].append(e)
                        i = i + 1
                except Exception:
                    break
                if i >= 50:
                    break
        except Exception as e:
            self._app.log.error('Exception: %s' % e)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

    @asyncio.coroutine
    def handle_isycontrolinfo(self, request):

        try:
            output = {'msg': 'SentientHome Event Engine',
                      'body': 'ISY Control Info Data in Cache'}
            output['control'] = defaultdict(int)
            # Count events by control type
            for event in self._memory.eventmemory['raw']['isy']:
                output['control'][event['Event.control']] += 1

        except Exception as e:
            self._app.log.error('Exception: %s' % e)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

    @asyncio.coroutine
    def handle_isystate(self, request):

        try:
            node = request.match_info.get('node')

            output = {'msg': 'SentientHome Event Engine',
                      'body': 'isy/[' + node + '] State Data',
                      'state': []}

            i = 0
            for e in self._memory.eventmemory['state']['isy'][node]:
                try:
                    output['state'].append(e)
                    i = i + 1
                except Exception:
                    break
                if i >= 50:
                    break
        except Exception as e:
            self._app.log.error('Exception: %s' % e)

        return web.Response(body=json.dumps(output,
                                            sort_keys=True).encode('utf-8'))

#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)
    print("syntax ok")

    exit(0)
