Sentient Home
=============

This is currently work in progress for a Sentient Home Automation project I am working on.

The project is primarily based on python.

The various feeders collect IoT data in realtime and micro batches. SOme leverage websockets while most poll various sources through REST/JSON.

The projects leverages an instance of InfluxDB that serves as a time series store for all incoming event and sensor data. Data integration and basic analytics have been the starting point of the project.

While there are many home automation products out there, all of them lack integration of various technologies. Apple's HomeKit has been announced earlier in 2014 but it has yet to be seen how it will get adopted and wether technologies form the likes of Google and NEST will get integrated at all.

The purpose of the project is to build a very SIMPLE integration solution leveraging python for most of the orchestration and event processing. The rules and workflows are code, UI is not planned for the initial version. However data visualization is done in a typical DevOps style leveraging Grafana dashboarding against the InfluxDB instance.

The project was started on an old Mac Mini that serves as the worker node for all realtime data collection. Going forward the majority of the processing is targeted for 1 or more Raspery PIs that can be distributed around the house and consume a fraction of the power of the old Mac Mini while also being a very cost effective platform for the kinds of IoT data integration needed for a single residence.

This repository will evolve over time as I add more capabilities to the realtime integration of the various technologies.

Technologies in Use
-------------------

These are some of the main technologies and components of the Home Automation project:

    INSTEON - Smart switches and dimmers, motion/water/power sensors
    ISY994 - Universal Devices INSTEON controller platform
    Rainforest Eagle - Realtime Smartgrid Power Sensor
    NEST - Thermostats and Smoke Detectors
    Netatmo - Personal Climate and Weather modules.
    Sonos - Amplifiers and Speakers
    Autelis - Pool Controller for Pentair Easytouch systems
    SmartThings - Hub to integrate Cloud and local services
    Wireless Sensor Tags - Temp/Humidity and motion sensors
