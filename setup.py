#!/usr/local/bin/python3 -u
__author__    = 'Oliver Ratzesberger <https://github.com/fxstein>'
__copyright__ = 'Copyright (C) 2016 Oliver Ratzesberger'
__license__   = 'Apache License, Version 2.0'

# Make sure we have access to SentientHome commons
import os

print('Checking node.js presence:')
if 0 != os.system('node -v'):
    print('node.js not present on system. Exiting...')
    quit()

print('Installing node.js dependencies:')
if 0 != os.system('npm install home'):
    print('Error installing node.js home module. Exiting...')
    quit()

if 0 != os.system('npm install iniparser'):
    print('Error installing node.js iniparser module. Exiting...')
    quit()

print('Installing Python3 dependencies')

if 0 != os.system('pip3 install -r dependencies.txt'):
    print('Error installing python3 dependencies. Exiting...')
    quit()

print('Create data directory')

if 0 != os.system('mkdir data'):
    print('Error creating local data directory. Exiting...')
    quit()

if 0 != os.system('mkdir data/nest'):
    print('Error creating local data directory. Exiting...')
    quit()

print('Finished installing dependencies.')
