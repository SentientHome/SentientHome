# Ansible Setup and Configuration for Raspberry PI

Once you have setup a barebones Raspberry PI (or multiple of them), its time to
setup and deploy Ansible.

In this particular document we are configuring an Ansible Master that will be
used to deploy the Sentient Home project as well as various other components
like Grafana, InfluxDB, logstash or elastic on one or more PIs or other types
of systems.

In this setup the Master node is merely a controller to deploy and update the
configuration, keep backups of all the other components but does not run the
Sentient Home project itself. Given the extreme low cost of Raspberry PIs we
recommend you too run a dedicated controller and deploy the various other
components of the project to one or more Raspberry PIs or servers of your
choosing.

1.  First we need to install some foundational elements including Docker and
    Ansible that don't come in the Raspian LITE image:

    ``` shell
    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install git
    sudo apt-get install python-dev
    sudo apt-get install python-pip
    sudo apt-get install python3
    sudo apt-get install python3-dev
    sudo apt-get install python3-pip
    sudo apt-get install keychain
    sudo apt-get install docker.io

    sudo apt-get install dnsmasq

    sudo pip install markupsafe
    sudo pip install ansible
    sudo pip3 install pubkey
    ```

    Note: We are also installing [pubkey](https://github.com/fxstein/pubkey)
    a Python 3 utility that helps us distribute the public keys amongst
    additional Raspberry Pis for password-less shh connections.

2.  Now we setup public & private keys to allow for password less ssh
    connections for all the systems involved.

    We recommend to follow the procedure outlined by [Github](https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/#platform-linux).

    Stick with the defaults to end up with a key pair called `id_rsa` and
    `id_rsa.pub`.

    To enable keychain for the newly create key add the following lines to the
    very end of your ~/.profile:

    ``` shell
    # run keychain
    eval `keychain --eval id_rsa`
    ```

3.  Next we add the newly create ssh key to our Github account (optional). That
    way we can commit changes and fixes to the Sentient Home project or any
    other Github project.

    To do so follow the instructions on [Github](https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/#platform-linux).

4.  Now that we have a secure key we distribute the public portion of it to all
    other Raspberry Pis we would like to use in our setup. This allows us to run
    the Sentient Home project on a single or as many as 10 or even more PIs
    depending on workload and the level of redundancy required.

    The idea is to be able to leverage distributed computing as much as possible
    just like we would in the Cloud.

    In order to distribute the keys simply run:

    ``` shell
    pubkey --auto
    ```

    Which should give you an output similar to:

    ``` shell
    INFO: pubkey file used: /home/pi/.ssh/id_rsa.pub
    INFO: pubkey REST server started at http://192.168.1.249:1080
    INFO: Timeout after 300s
    Remote host command:

    curl -s -S 192.168.1.249:1080 >> ~/.ssh/authorized_keys

    Press ctrl-C to stop.
    ```

    For the next 300s pubkey will make the above key available to other
    computers to download.

    Head on over to the other Rapsberry(s) and simply run:

    ``` shell
    mkdir -p ~/.ssh
    curl -s -S 192.168.1.249:1080 >> ~/.ssh/authorized_keys
    ```

    Note: replace the curl line with the one pubkey shows.

    With that you have established password less ssh connections from you main
    controller. From here on out Ansible will be our choice to manage and
    maintain one or many PIs

5.  With the basics in place lets clone the entire Sentient Home project onto
    our deployment master:

    ``` shell
    cd
    git clone git@github.com:fxstein/SentientHome.git
    ln -s ~/SentientHome/deploy/raspberry/ansible
    sudo mkdir -p /etc/ansible
    cd /etc/ansible
    sudo ln ~/ansible/hosts
    cd
    ```
