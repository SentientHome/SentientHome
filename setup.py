#!/usr/local/bin/python -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2015 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os

print 'Checking node.js presence:'
if 0 != os.system('node -v'):
    print 'node.js not present on system. Exiting...'
    quit()

print 'Installing node.js dependencies:'
if 0 != os.system('npm install home'):
    print 'Error installing node.js home module. Exiting...'
    quit()

if 0 != os.system('npm install iniparser'):
    print 'Error installing node.js iniparser module. Exiting...'
    quit()

print 'Installing Python3 dependencies'

if 0 != os.system('pip3 install asyncio'):
    print 'Error installing python3 asyncio package. Exiting...'
    quit()

if 0 != os.system('pip3 install aiohttp'):
    print 'Error installing python3 aiohttp package. Exiting...'
    quit()

print 'Finished installing dependencies.'
