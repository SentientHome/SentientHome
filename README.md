SentientHome
============

[![Build Status](https://travis-ci.org/fxstein/SentientHome.svg?branch=develop)](https://travis-ci.org/fxstein/SentientHome)

This is currently work in progress for a Sentient Home Automation project I am working on. It is still in its infancy and has not been packaged for easy deployment.

[![Sentient Home Sample Dashboard](https://raw.githubusercontent.com/fxstein/SentientHome/master/samples/Home.Dashboard.Small.png)](https://raw.githubusercontent.com/fxstein/SentientHome/master/samples/Home.Dashboard.png)

The project is primarily based on python.

It is written with simplicity in mind, rather than perfection. Less is more. Technologies for Cloud and DevOps that exist should be leveraged as much as possible.

As such the project makes use of simple components like supervisor, collectd, InfluxDB and Grafana - to name a few. Ultimately it should not make any difference if it is deployed in private or public cloud, even though we strongly believe Home Automation data does not belong in public clouds. This is your most private data and you should be in control of it.

As we have learned from various cloud based solutions, the availability of internet connections and cloud capacity rarely allows cloud based solution to operate at or above 98% of availability. For an automated home that relies on events to happen 24x7 that is simply not acceptable.

The project has been developed on an old Mac Mini as the primary platform but should ultimately be available on any python enabled platform. I am especially targeting the Raspberry PI as one of the platforms to leverage for this project.

An Overview
-----------

The project has been designed with ultimate modularity in mind. Individual components run as stand alone servies on one or multiple HW platforms. RESTful/JSON are the servie APIs of choice. Everything but the event store can be run on a single Raspberry PI (the RPI 2 might change that) or alternatively load can be balanced over multiple Raspberry PIs or event mixed configurations of varying processing platforms. More on that in the upcoming documentation.

The various feeders collect IoT and sensor data in realtime and micro batches. Some leverage websockets while most poll various sources through REST/JSON, SOAP/XML, RPC or SNMP. Feeders are meant to be simple and small. Most will be less than 50-100 lines of python code. Get some data or listen to a socket, put it into a simple time series JSON format and hand it to the event handler.

An instance of InfluxDB is leveraged that serves as a time series event store for all incoming event and sensor data. Data integration and basic analytics have been the starting point of the project.

In parallel all events are posted to an event engine that allows for the implementation of simple event based rules. The event engine assembles an in-memory cache of the last 24+h and will soon be extensible via simple python plugins. This will allow for feed specific state caches to simply the implementation of time series & state specific rulesets. Virtually all existing home automation or sensor data automation systems allow for very basic rules and variables. However most logic required for smart automation requires the context of time and state over time that none of them support in simple terms.

For example:
> You want to turn on lights/scenes at sunset every day. A primitive rule to start with. Pretty much all decent automation systems allow for such a rule to be implemented. However in real life that rule will not be satisfactory in many situations. On certain days you will have already manually turned on some of the lights before sunset. Without extra logic the sunset will trigger a reset of the scene(s) to the predefined level, independent whether a human has interacted with some or all of the scene(s) just minutes before. Lets take a kitchen setup: You have potentially multiple down lights, countertop lights and maybe a chandelier or two. You put them into an automatic scene that should dim the chandeliers to 50%, turn on the countertop lights at 75% and have the down-lights off. Nice scene to automatically come on every night.
> Now bring in the human element that a person just 10 min earlier put on all lights at 100% because of activities that require more light. The rule we laid out of course has no concept of human interaction and will reset the lights at sunset to 50%/75%/0% respectively. You go through that a few times and you will become pretty annoyed every time this happens.
> So the rule needs to be extended for example to only set the scene if no human interaction has happened within the past 20 min that left lights at a certain on level.

> This is where it gets pretty tricky very quickly. Most home automation solutions will require the use of state variables, timeout counters and multiple programs to accomplish this. While doable for a single room, if you want this type of behavior at scale, it quickly gets way too complex to implement.

> With the time-series event and state cache of the Sentient Home event engine, this logic becomes a very simple loop back over time aborted if the time difference is more than e.g. the 20 min in combination with e.g. motion sensor data. Because every event rule has access to the history of events and states over the past 24h, timeseries based behaviors are very simple to implement. This is currently work in progress and not completed, but hopefully you get the gist.

Due to the nature of a single home producing low volumes of data for each instance, we have avoided added overhead or deploying complex technologies that can scale to very large volumes. This project is meant to be close to the edge on very lightweight processing platforms.

Further aggregation of multiple homes would leverage technologies like Kafka, Storm, Samsa or Spark. But that is beyond the scope of this implementation.

Why another home automation platform?
-------------------------------------

While there are many home automation products out there, all of them lack integration of various technologies. Apple's HomeKit has been announced earlier in 2014 but it has yet to be seen how it will get adopted and wether technologies from the likes of Google and NEST will get integrated at all.

The purpose of the project is to build a very SIMPLE integration solution leveraging python for most of the orchestration and event processing. ANY technology that has some sort of an open API should be integratable in realtime
The rules and workflows are code, UI is not planned for the initial version. However data visualization is done in a typical DevOps style leveraging Grafana dash boards against an InfluxDB instance.

The project was started on an old Mac Mini that serves as the worker node for all realtime data collection. Going forward the majority of the processing is targeted for 1 or more Rasperry PIs that can be distributed around the house and consume a fraction of the power of the old Mac Mini while also being a very cost effective platform for the kinds of IoT data integration needed for a single residence.

This repository will evolve over time as I add more capabilities to the realtime integration of the various technologies.

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

All our projects follow the [GitFlow branching model][gitflow-model], from development to release. If you are not familiar with it, there are several guides and tutorials to make you understand what it is about.

You will probably want to get started by installing [this very good collection of git extensions][gitflow-extensions].

What you mainly want to know is that:

- All the main activity happens in the `develop` branch. Any pull request should be addressed only to that branch. We will not consider pull requests made to the `master`.
- It's very well appreciated, and highly suggested, to start a new feature branch whenever you want to make changes or add functionalities. It will make it much easier for us to just checkout your feature branch and test it, before merging it into `develop`


License
-------

Copyright (C) 2015 Oliver Ratzesberger

SentientHome is released under the [Apache License, Version 2.0][1]

  [1]: https://github.com/fxstein/SentientHome/blob/master/LICENSE.md
