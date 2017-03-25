SentientHome
============

[![Build Status](https://travis-ci.org/SentientHome/SentientHome.svg?branch=develop)](https://travis-ci.org/SentientHome/SentientHome)

This is currently work in progress for a Sentient Home Automation project I am working on. It is still in its infancy and has not been packaged for easy deployment.

[![Sentient Home Sample Dashboard](https://raw.githubusercontent.com/SentientHome/SentientHome/master/samples/Home.Dashboard.Small.png)](https://raw.githubusercontent.com/fxstein/SentientHome/master/samples/Home.Dashboard.png)

The project is primarily based on python.

It is written with simplicity in mind, rather than perfection. Less is more. Technologies for Cloud and DevOps that exist should be leveraged as much as possible.

As such the project makes use of simple components like supervisor, collectd, InfluxDB and Grafana - to name a few. Ultimately it should not make any difference if it is deployed in private or public cloud, even though we strongly believe Home Automation data does not belong in public clouds. This is your most private data and you should be in control of it.

An Overview
-----------

The project has been designed with modularity in mind. Individual components run as stand alone services on one or multiple HW platforms. RESTful/JSON are the service APIs of choice. Everything but the event store can be run on a single Raspberry PI (the RPI 2 might change that) or alternatively load can be balanced over multiple Raspberry PIs or event mixed configurations of varying processing platforms. More on that in the upcoming documentation.

The various feeders collect IoT and sensor data in realtime and micro batches. Some leverage websockets while most poll various sources through REST/JSON, SOAP/XML, RPC or SNMP. Feeders are meant to be simple and small. Most will be less than 50-100 lines of python code. Get some data or listen to a socket, put it into a simple time series JSON format and hand it to the event handler.

An instance of InfluxDB is leveraged that serves as a time series event store for all incoming event and sensor data. Data integration and basic analytics have been the starting point of the project.

In parallel all events are posted to an event engine that allows for the implementation of simple event based rules. The event engine assembles an in-memory cache of the last 24+h and will soon be extensible via simple python plugins. This will allow for feed specific state caches to simply the implementation of time series & state specific rulesets. Virtually all existing home automation or sensor data automation systems allow for very basic rules and variables. However most logic required for smart automation requires the context of time and state over time that none of them support in simple terms.

IoT Technologies in Use
-----------------------

These are some of the main technologies and components of the Home Automation project:

    APC UPS - APC (Schneider Electric) UPS Network Managment Card 2 SNMP
    Autelis - Pool Controller for Pentair Easytouch systems
    Google Finance - Realtime financials for stocks, indices and currencies
    INSTEON - Smart switches and dimmers, motion/water/power sensors
    ISY994 - Universal Devices INSTEON controller platform
    NEST - Thermostats and Smoke Detectors
    Netatmo - Personal Climate and Weather modules.
    Philips Hue - Smart controlable lighting (TBD)
    Rainforest Eagle - Realtime Smartgrid Power Sensor
    Sonos - Amplifiers and Speakers (TBD)
    SMA Webbox - Realtime metrics for SMA PV Solar systems
    SmartThings - Hub to integrate Cloud and local services (TBD)
    Ubiquiti mFi - Ubiquity mFi sensors and devices
    Ubiquiti Unifi - Ubiquiti Unifi LAN/WAN equipment (TBD)
    Ubiquiti Unifi Video - Ubiquiti Unifi Video equipment (TBD)
    USGS - Realtime geological data feeds
    Wireless Sensor Tags - Temp/Humidity and motion sensors (TBD)

Contributing
------------

We appreciate any contribution to SentientHome, whether it is related to bugs, grammar, or simply a suggestion or improvement.
However, we ask that any contributions follow our simple guidelines in order to be properly received.

All our projects follow the [GitFlow branching model](http://nvie.com/posts/a-successful-git-branching-model/), from development to release. If you are not familiar with it, there are several guides and tutorials to make you understand what it is about.

You will probably want to get started by installing [this very good collection of git extensions][gitflow-extensions].

What you mainly want to know is that:

- All the main activity happens in the `develop` branch. Any pull request should be addressed only to that branch. We will not consider pull requests made to the `master`.
- It's very well appreciated, and highly suggested, to start a new feature branch whenever you want to make changes or add functionalities. It will make it much easier for us to just checkout your feature branch and test it, before merging it into `develop`


License
-------

Copyright (C) 2015 Oliver Ratzesberger

SentientHome is released under the [Apache License, Version 2.0][1]

  [1]: https://github.com/SentientHome/SentientHome/blob/master/LICENSE.md
