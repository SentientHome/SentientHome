# Configuration

As described in the Raspberry PI README we are combing the Model 2 or 3 B with
a Samsung SSD 250/500GB or larger. Here is a simple step by step guide on how
to configure the setup from scratch.

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
    frequently. Make sure you use the most recent version.

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
Raspberry PI 2/3. Make sure your PI is connected to the network/internet via
patch cable, as it will require an active internet connection for the remainder
of the initial setup.

## Finalizing the Boot Image Setup

Now that we have a working boot SD card for our brand new Raspberry PI, the
next steps will be performed on the Raspberry itself.

For that, install the device in the case of your choosing, install the brand
new boot SD card, connect keyboard, mouse (optional) and a monitor.

Once wired up, connect the Raspberry to power and watch it boot up. You should
see the red LED light up permanently and the green LED flashing randomly,
whenever the device performs IO operations - as in reads or writes from the
SD card.

1.  Initial bootup will only take a few seconds and you will find yourself at
    the login prompt: `raspberrypi login:`

    The default credentials of the Raspberry PI are: username: `pi` and
    password `raspberry`. Enter those credentials and you should be
    successfully logged into your brand new Raspberry PI.

2.  This next step you should consider mandatory, must have, no time to
    procrastinate:

    __Now is the time to change the password! Don't put this off
    until later. Later means you are running around with a big security hole
    target on your forehead. IoT and Home Automation are already known for
    their weak information security standards. Don't contribute with yet
    another easy to hack system in the world.__

    in order to change the default user password simply type in:
    `passwd⏎` followed by the current password `raspberry` and then two
    iterations of the new password. Consider something decently strong. Most
    password generators give you various options. Multiple words separated by
    a simple sign are a very good start and usually easy to remember. Choose
    something like 3 or 4 words minimum: `align_corrode_brim` but make it your
    own, hard to guess combination.
    A password generator and wallet are definitely the pro choice.

3.  Now that the system is no longer open to the world, lets setup the basics
    with the built in config tool: `sudo raspi-config⏎`

4.  Once we are in the config screen we expand the boot volume to its maximum
    size. A PI that runs out of storage starts doing very weird and bad things:
    Choose `1 Expand Filesystem⏎` changes to the size will become active at
    the very next reboot.

5.  While there are lots of options to choose from, we recommend you keep it
    simple, predictable and hopefully reliable. For example Overclocking should
    be a __BIG NO-NO__. We dont need a fraction more performance, we need
    reliability for this little computer to run 24x7x365.

    The only thing we really want to get done before we reboot is to make sure
    we have the latest version of the update tool by selecting:
    `9 Advanced Options⏎` followed by `A0 Update⏎`

6.  The final step for the reboot inside the config utility is to make sure our
    SSH server is enabled. From here on out we want the ability to SSH into
    the PI without the need for local keyboard, mouse or monitor.

    To do so simply select `9 Advanced Options⏎` followed by `A4 SSH⏎` then
    select `Enable⏎` and `Ok⏎` and close out the config utility via `Finish⏎`.

7.  Back at the command prompt its now a good idea to perform a full reboot.
    Simply enter `sudo reboot⏎` and watch the PI run through a quick restart
    sequence.

8.  Once rebooted, log back into the PI with username `pi` and your new __secret
    password__. Alternatively all steps from here on out can be performed via
    SSH from a remote computer, e.g. a Mac terminal session.

9.  Now we are updating all the key packages as well as the firmware by running
    the following commands:

    ``` shell
    sudo su⏎
    apt-get update⏎
    apt-get upgrade⏎
    apt-get install rpi-update⏎
    rpi-update⏎
    reboot⏎
    ```

    These will update all core components of our setup to the very latest
    available versions. And reboot the computer to apply the changes made.

We now have a basic working and initialized setup that we can leverage for one
or multiple Raspberry PIs.
