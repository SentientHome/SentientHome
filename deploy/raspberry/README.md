# Raspberry PI

This deployment option focuses on the
[Raspberry PI](https://www.raspberrypi.org). Especially since models
[B 2](https://www.raspberrypi.org/products/raspberry-pi-2-model-b/) and
[B 3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) have been
release in 2015 and 2016 respectively, the Raspberry PI has become a formidable
platform for IoT and all things Home Automation.

This section of the project focuses on how to configure one or multiple
Raspberry PIs in the most suitable way for the deployment of
[Sentient Home](https://github.com/fxstein/SentientHome).

## Sample configuration

The Raspberry PI universe has countless options for extensions, cases, memory,
storage, power, ... and so forth.

Here we are describing an advanced Raspberry PI configuration example that
should work very well for most Sentient Home applications.

As of this writing we recommend to go with a Raspberry PI Model B 3. With its
quad-core ARM based CPU, 1GB of RAM and embedded WiFi it has become our #1
choice.

You can purchase the PI from many online websites, if you are in a hurry you
might want to get it through Amazon Prime. CanaKit makes a complete starter kit
that comes with everything to run the PI except for Monitor and Keyboard:
[CanaKit Raspberry Pi 3 Complete Starter Kit - 32 GB Edition](http://www.amazon.com/CanaKit-Raspberry-Complete-Starter-Kit/dp/B01C6Q2GSY)

The Kit comes with 32GB memory card, USB adapter, case, power supply, HDMI
cable and some rudimentary documentation.

If you prefer other options than what comes with the Kit here are a few choices
that we like most:

### Aluminum case

We prefer a more sturdy aluminum case over the cheaper plastic versions. In
particular this model's fit and finish combined with a little micro fan and it's
mounting options has made it our #1 choice:
[Tontec® Raspberry Pi 2/3 Case](http://www.amazon.com/Tontec®-Raspberry-Aluminum-Protective-Cooling/dp/B00PALBNY6)
About the only thing we would like to see changed is the fact that it comes with
double sides tape to mount the fan. Four little screws would definitely beat
that.

Other than that the perfect case of a solid Home Automation project.

### PoE Power supply

The biggest drawback of the Raspberry Pi is the lack of any form of ON/OFF
switch. Not that we are planning to turn it much off, but having to pull cables
in order to power cycle the unit is not a good setup.
Since more and more networking equipment, sensors and cameras are switching to
PoE (Power over Ethernet) we decided to do the same with the Raspberry PI.
Here is our choice to power the Raspberry PI via PoE:
[802.3af Poe Splitter for Remote USB Power over Ethernet for Raspberry PI](http://www.amazon.com/Splitter-Ethernet-MicroUSB-Raspberry-WT-AF-5v10w/dp/B019BLMWWW)

### SSD storage

Since the Sentient Home is all about data collection and as we are listening to
event data from within the Home as well as the rest of the world, we need
reliable storage that integrates well with the Raspberry PI.

While current models of the PI only support USB 2 and as such are limited to
20-30MB/s and as such most SSDs are overkill from a performance perspective,
the lower power draw and small size of some of the models make them a perfect
fit for a project like this. Most come with USB3 interfaces that are also a
decent investment for the future.

Our choice for the Rasperry PI is the
[Samsung T3 Portable 250GB USB 3.0 External SSD](http://www.amazon.com/Samsung-Portable-External-MU-PT250B-AM/dp/B01AVF6WN2)
available in sizes 250GB, 500GB and 1TB
