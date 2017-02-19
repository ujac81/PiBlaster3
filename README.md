# PiBlaster3

3rd version of PiBlaster software -- access point / web version

Install instructions -- updated 2016/12/16

# Set up Raspberry Pi
Install latest raspbian

## Access Point Mode
Example set for net 192.168.207.0

**Note:** settings configured for wlan1 -- if you have no raspi model #3, you might want to switch to wlan0.

    $ sudo aptitude install hostapd udhcpd

/etc/udhcpd.conf

    start           192.168.207.20
    end             192.168.207.254
    interface       wlan1
    opt subnet      255.255.255.0
    opt router      192.168.207.1
    opt lease       864000
    opt dns         192.168.207.1

/etc/default/udhcpd

    #DHCPD_ENABLED="no"

/etc/network/interfaces

    iface wlan1 inet static
      address 192.168.207.1
      netmask 255.255.255.0
      broadcast 192.168.207.255

/etc/hostapd/hostapd.conf

    interface=wlan1
    driver=rtl871xdrv
    ssid=PiBlaster3
    hw_mode=g
    channel=6
    macaddr_acl=0
    auth_algs=1
    ignore_broadcast_ssid=0
    wpa=2
    wpa_passphrase=SECRET_PASS_PHRASE
    wpa_key_mgmt=WPA-PSK
    rsn_pairwise=CCMP

/etc/default/hostapd

    DAEMON_CONF="/etc/hostapd/hostapd.conf"

Enable services at boot

    $ sudo update-rc.d hostapd enable
    $ sudo update-rc.d udhcpd enable

### Nameserver
To make web interface accessible via ***pi.blaster***.

    $ sudo aptitude install bind9

/etc/bind/named.conf.local

    zone "blaster" IN {
            type master ;
            file "/etc/bind/zone.blaster";
    };
    zone "0.207.168.192.in-addr.arpa" IN {
            type master ;
            notify no ;
            file "/etc/bind/zone.0.207.168.192.in-addr.arpa";
    };

/etc/bind/zone.blaster

    $ORIGIN blaster.
    $TTL 3600       ; 1 hour
    @                     IN SOA  pi.blaster. pi.pi.blaster. (
                                    2016121601 ; serial
                                    3600       ; refresh (1 hour)
                                    3600       ; retry (1 hour)
                                    604800     ; expire (1 week)
                                    86400      ; minimum (1 day)
                                    )

    @               IN NS   pi.blaster.
    pi              IN A    192.168.207.1

/etc/bind/zone.0.207.168.192.in-addr.arpa

    $TTL 2d
    @               IN SOA          pi.blaster.    pi.pi.blaster. (
                                    2016121603      ; serial
                                    3h              ; refresh
                                    1h              ; retry
                                    1w              ; expiry
                                    1d )            ; minimum

    @       IN NS   pi.blaster.
    1       IN PTR  pi.blaster.

## Reverse Proxy
Nginx will be used as revere proxy and delivery of mp3 files.
Configuration will be done, when PiBlaster3 is installed.

    $ sudo aptitude install nginx
    $ sudo update-rc.d nginx enable

## Required Packages

    $ sudo aptitude install python3 python3-pip python3-virtualenv virtualenv nginx coffeescript ruby-sass mpd mpc usbmount git
    $ sudo pip3 install django==1.10.5

At least pypugjs 4.1 required (if pypugjs==4.1 installable via pip3, you might use this directly)

    $ sudo pip3 install git+https://github.com/matannoam/pypugjs.git@master
    $ sudo pip3 install django_compressor
    $ sudo pip3 install uwsgi
    $ sudo pip3 install python-mpd2

## PiBlaster3 software

    $ cd /opt
    $ sudo chown pi:pi .
    $ git clone https://github.com/ujac81/PiBlaster3.git

# Configuration

    $ cd /opt/PiBlaster3
    $ python3 manage.py migrate
    $ python3 manage.py migrate static_precompiler

## NGINX

    $ cd /etc/nginx/sites-enabled/
    $ sudo rm default
    $ sudo ln -s /opt/PiBlaster3/conf/site-piblaster
    $ sudo service nginx restart

## UWSGI

    $ sudo cp /opt/PiBlaster3/conf/piblaster.service /etc/systemd/system

## MPD
Link directories to scan to mpd library and update it.

    $ sudo ln -s /local /var/lib/mpd/music/local
    $ sudo ln -s /media/usb0 /var/lib/mpd/music/usb0
    $ sudo ln -s /media/usb1 /var/lib/mpd/music/usb1
    $ mpc update

# Developer Notes

## Create new django project

    $ sudo pip3 install django=x
    See version list
    $ sudo pip3 install django=1.10.5

## Restart service

## Run piblaster3 server from command line
To see full debugging output and interact with django server:

    $ sudo service piblaster stop
    $ cd /opt/PiBlaster3
    $ ./manage.py runserver 0.0.0.0:8000

Connect to http://YOUR_PI_HOST:8000

## PyPugJS templates
All templates are built using the pypugjs(https://github.com/matannoam/pypugjs) interface for pugjs(https://pugjs.org/api/getting-started.html)

Use pypugjs file.pug to check output.

## Coffeescript / Sass
Javascript and CSS files are compiled by django_compress http://django-compressor.readthedocs.io/en/latest/ .
Sass/coffeescript files are handled via COMPRESS_PRECOMPILERS in settings.py.
