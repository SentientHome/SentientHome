# Configuration

As described in the Raspberry PI README we are combing the Model 2 or 3 B with
a Samsung SSD 250/500GB or larger. Here is a simple step by step guide on how
to configure the setup from scratch.

TODO: Ansible playbook

## Initial SD Card Setup

We recommend to start with a clean image of the latest version of
[RASPBIAN](https://www.raspberrypi.org/downloads/raspbian/). While you can get
preloaded SD Cards with Raspberry NOOBS on it, they are usually already outdated
by them time you get them and more importantly include a lot of software and
extras that just get in the way of storage and a clean install.

[raspberrypi.org](https://www.raspberrypi.org) has some great
[Installation](https://www.raspberrypi.org/documentation/installation/installing-images/mac.md)
procedures for the various Operation Systems out there.

### OS X El Capitan

Here a quick summary for the latest version of OS X 10.11.x

1.  We recommend starting with downloading the latest
[RASPBIAN LITE](https://downloads.raspberrypi.org/raspbian_lite_latest)

2.  Next insert a new SD Card e.g.
[SanDisk Ultra 32GB UHS-I/Class 10 Micro](http://www.amazon.com/SanDisk-Ultra-SDSDQUAN-032G-G4A-Memory-Adapter/dp/B00M55C0NS)
with a suitable USB adapter into one of your Macs USB ports.

3.  Open a Terminal window.

4.  Now make sure you are in your users home directory: `cd⏎`

5.  From there head to your Donwloads folder: `cd Downloads⏎`

6.  Find the recently downloaded Raspian image: `ls *raspbian*lite.zip⏎`

    e.g. `2016-03-18-raspbian-jessie-lite.zip`

    Note: The filename contains the date of the release and will therefor change
    frequently. Make sure you use the mist recent version.

7.  Unzip the package: `unzip 2016-03-18-raspbian-jessie-lite.zip⏎`

8.  Validate that the image file has been created: `ls *raspbian*lite.img⏎`

    e.g. `2016-03-18-raspbian-jessie-lite.img`

    Note: Like before the filename contains the date of the release.

9.  Now we look up the BSD name of the SD Card we want to apply the image to:
    `diskutil list⏎`

    Look for and entry like `/dev/disk? (external, physical):` where `?` and
    number like `2` or `3` ... In many cases the disk will be named
    `dev/disk2` or `dev/disk3`unless your system has multiple internal or
    external storage devices.

    In order to make sure you are looking at the correct disk entry make sure
    the entry is marked `external` and the SIZE matches the the capacity of the
    SD card. IN our case the 32GB SD Card shows up as `31.9 GB`

    Note: In some cases specific SD cards only work with some USB SD card
    adapters. If your SD card does not show up, it is possible that the SD card
    USB adapter is not working with this specific type of SD card.

10. Next we unmount the disk. In our case the BSD disk name is `dev/disk2`
    This is how we unmount the device: `diskutil unmountDisk /dev/disk2⏎`

    Look for confirmation: `Unmount of all volumes on disk2 was successful`

11. Now we copy the image to the SD card:
    `sudo dd bs=1m if=2016-03-18-raspbian-jessie-lite.img of=/dev/disk2⏎`

    Note: As mentioned before replace the img name with the version you have
    downloaded and the BSD disk name with the one from your system.
    Also this process can take some time - as in several minutes. To get
    realtime updates on progress hit `<control>+T`

Now you should have a working image to perform a clean, initial boot-up of your
Raspberry PI 2/3. If you have chose the Raspbian LITE image, make sure your PI
is connected to the network/internet via patch cable, as it will require the
download of additional components during install.  
