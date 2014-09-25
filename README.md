Simple Smart Home Automation Listener
=====================================

This is currently work in progress for a Smart Home Automation project I am working on.

The Listener Setup collects data from varios home sources and stores them in realtime in an InfluxDB instance.

I am hosting the entire project on an old Mac Mini that serves as the worker node for all realtime datacollection.

I am currently using Grafana 1.8.0 to graph most of the event data in a realtime dashboard.

This repository will evolve over time as I add more capabilities to the realtime integration of the various technologies.

Technologies in Use
-------------------

These are some of the main technologies and components of the Home Automation project:

    INSTEON - Smart switches and dimmers, motion/water/power sensors
    ISY994 - Universal Devices INSTEON controller platform
    Rainforest Eagle - Realtime Smartgrid Power Sensor
    NEST - Thermostats and Smoke Detectors
    Sonos - Amplifiers and Speakers
    Autelis - Pool Controller for Pentair Easytouch systems
    SmartThings - Hub to integrate Cloud and local services
    Wireless Sensor Tags - Temp/Humidity and motion sensors
