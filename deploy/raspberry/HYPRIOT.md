# Setting up a new Rapberry PI using Hypriot OS

As we are going to base most of the Home's setup on docker we have chose the
most optimized PI OS for docker: Hypriot OS. It is also extremely easy to setup
from a Mac.

1.  Flashing a new SD Card with the latest Hypriot image

    Look up the latest available image: [Hypriot OS Downloads](http://blog.hypriot.com/downloads/)
    As of this writing that is:
    `https://downloads.hypriot.com/hypriot-rpi-20160306-192317.img.zip`

    With that we are going to flash a new SD Card using the
    [Hypriot flash utility](https://github.com/hypriot/flash)

    For the new host name we chose `master` (in anticipation of eventually
    running a second instance for redundancy as `master`)

    ```bash
    flash --hostname master https://downloads.hypriot.com/hypriot-rpi-20160306-192317.img.zip
    ```

    Note: The host name will be different for the various types of nodes you
    will setup. Master will be our go to host that will be used to setup and
    configure the entire Sentient Home eco system using Ansible.

    Follow the instructions of the flash utility and within a few minutes the
    raw boot image is ready.

2.  Install the SD Card into a Raspberry PI of your choice and boot it up. For
    now we assume you have an existing DHCP server on your local network that
    will provide this new PI with a temporary IP address.

3.  Finding the new Raspberry PI

    To find the PI on the local network simply run:

    ```shell
    function getip() { (traceroute $1 2>&1 | head -n 1 | cut -d\( -f 2 | cut -d\) -f 1) }
    PI_IP=$(getip master.local)
    echo $PI_IP
    ```

4.  Adding your SSH public key to the PI

    With the `$PI_IP` variable set we can simply execute:

    ```bash
    ssh-keygen -R $PI_IP
    ssh-copy-id -oStrictHostKeyChecking=no -oCheckHostIP=no root@$PI_IP
    ```

    Note: The base image will come up with root password `hypriot`

5.  Change the root password

    __Don't procrastinate now is the time to change the root password. Do not
    put this off until later. Once on the network your device is vulnerable.__

    ```bash
    ssh root@$PI_IP passwd
    ```

Note: IN some cases you might have to refresh you Mac's local DNS cache in order
to make new or updated host work with DNS names.
See the [Apple Support Article: Reset the DNS cache in OS X](https://support.apple.com/en-us/HT202516)
for more information
