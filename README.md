SentientHome
============

[![Build Status](https://travis-ci.org/fxstein/SentientHome.svg?branch=master)](https://travis-ci.org/fxstein/SentientHome)

This is currently work in progress for a Sentient Home Automation project I am working on.

The project is primarily based on python.

It is written with simplicity in mind, rather than perfection. Less is more. Technologies for Cloud and DevOps that exist should be leveraged as much as possible.

As such the project makes use of simple components like supervisor, collectd, InfluxDB and Grafana - to name a few. Ultimately it should not make any difference if it is deployed in private or public cloud, even though we strongly believe Home Automation data does not belong in public clouds. This is your most private data and you should be in control of it.

As we have learned from various cloud based solutions, the availability of internet connections and cloud capacity rarely allows cloud based solution to operate at or above 98% of availability. For an automated home that relies on events to happen 24x7 that is simply not acceptable.

The project has been developed on an old Mac Mini as the primary platform but should ultimately be available on any python enabled platform. I am especially targeting the Raspberry PI as one of the platforms to leverage for this project.

An Overview
-----------

The project has been designed with ultimate modularity in mind. Individual components run as stand alone programs on one or multiple HW platforms. Everything but the event store can be run on a single Raspberry PI or alternatively load can be balanced over multiple Raspberry PIs or event mixed configurations of varying processing platforms. More on that in the upcoming documentation.

The various feeders collect IoT data in realtime and micro batches. Some leverage websockets while most poll various sources through REST/JSON or Soap. Feeders are meant to be simple and small. Most will be less than 50-100 lines of python code. Get some data or listen to a socket, put it into a simple time series JSON format and hand it to the event handler.

The projects leverages an instance of InfluxDB that serves as a time series event store for all incoming event and sensor data. Data integration and basic analytics have been the starting point of the project.

In parallel all events are posted to an event engine that allows for the implementation of simple event based rules.

Due to the nature of a single home producing low volumes of data for each instance, we have avoided added overhead or deploying complex technologies that can scale to very large volumes. This project is meant to be close to the edge on very lightweight processing platforms.

Further aggregation of multiple homes would leverage technologies like Kafka, Storm, Samsa or Spark. But that is beyond the scope of this implementation.

Why another home automation platform?
-------------------------------------

While there are many home automation products out there, all of them lack integration of various technologies. Apple's HomeKit has been announced earlier in 2014 but it has yet to be seen how it will get adopted and wether technologies from the likes of Google and NEST will get integrated at all.

The purpose of the project is to build a very SIMPLE integration solution leveraging python for most of the orchestration and event processing. The rules and workflows are code, UI is not planned for the initial version. However data visualization is done in a typical DevOps style leveraging Grafana dash boards against an InfluxDB instance.

The project was started on an old Mac Mini that serves as the worker node for all realtime data collection. Going forward the majority of the processing is targeted for 1 or more Rasperry PIs that can be distributed around the house and consume a fraction of the power of the old Mac Mini while also being a very cost effective platform for the kinds of IoT data integration needed for a single residence.

This repository will evolve over time as I add more capabilities to the realtime integration of the various technologies.

IoT Technologies in Use
-----------------------

These are some of the main technologies and components of the Home Automation project:

    INSTEON - Smart switches and dimmers, motion/water/power sensors
    ISY994 - Universal Devices INSTEON controller platform
    Rainforest Eagle - Realtime Smartgrid Power Sensor
    NEST - Thermostats and Smoke Detectors
    Netatmo - Personal Climate and Weather modules.
    Sonos - Amplifiers and Speakers
    Philips Hue - Smart controlable lighting
    Autelis - Pool Controller for Pentair Easytouch systems
    SmartThings - Hub to integrate Cloud and local services
    Wireless Sensor Tags - Temp/Humidity and motion sensors

License
-------

Copyright (C) 2015 Oliver Ratzesberger

SentientHome is released under the [Apache License, Version 2.0][1]

  [1]: https://github.com/fxstein/SentientHome/blob/master/LICENSE.md
