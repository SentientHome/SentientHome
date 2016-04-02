# DNS & DHCP configuration for the Raspberry PI

Since you will need an easy yet flexible way to deal with DHCP requests and a
simple DNS setup for the home in order to address the various resources in the
house, this is a simple setup guide to configure a master node to serve as the
local DHCP and DNS server.

## Installing dnsmasq on the Raspberry PI

Starting from a working base configuration these are the steps to deploy
`dnsmasq` on a PI node to server as the local DHCP and DNS server/forwarder:

1.  Installing `dnsmasq`

    ```bash
    sudo apt-get install dnsmasq
    ```

2.  Configuring `dnsmasq`

    `dnsmasq` is configured with the following files:

    ```bash
    /etc/dnsmasq.conf # main configuration
    /etc/resolv.conf  # DNS forward
    /etc/hosts        # Static IP addresses
    /etc/ethers       # Static DHCP mappings
    ```
