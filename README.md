# PiBlaster3

3rd version of PiBlaster software -- access point / web version

Install instructions -- updated 2016/12/16

# Set up Raspberry Pi
Install latest raspbian

## Access Point Mode
Example set for net 192.168.207.0

**Note:** settings configured for wlan1 -- if you have no raspi model #3, you might want to switch to wlan0.

    $ sudo aptitude install hostapd dnsmasq

Prevent dhcpd on wlan interface. At the bottom of /etc/dhcpcd.conf add

    denyinterfaces wlan1

/etc/network/interfaces

    iface wlan1 inet static
      address 192.168.207.1
      network 192.168.207.0
      netmask 255.255.255.0
      broadcast 192.168.207.255

Use hostapd.conf from PiBlaster3 installation to /etc/default/hostapd make sure WPA passphrase changes via piadmin are valid.

    DAEMON_CONF="/opt/PiBlaster3/conf/hostapd.conf"

/etc/hosts

    192.168.207.1 pi.blaster pi

/etc/resolv.conf

    nameserver 127.0.0.1

/etc/dnsmasq.conf

    interface=wlan1
    listen-address=127.0.0.1
    listen-address=192.168.207.1
    bind-interfaces
    #server=8.8.8.8
    #domain-needed
    #bogus-priv
    dhcp-range=192.168.207.50,192.168.207.150,12h
    local=/blaster/
    domain=blaster
    expand-hosts
    address=/#/192.168.207.1

Enable services at boot

    $ sudo update-rc.d hostapd enable
    $ sudo update-rc.d dnsmasq enable

## Reverse Proxy
Nginx will be used as revere proxy and delivery of mp3 files.
Configuration will be done, when PiBlaster3 is installed.

    $ sudo aptitude install nginx
    $ sudo update-rc.d nginx enable

## PostgreSQL Database
PiBlaster 3 software uses pSQL database to store settings and other things like upload queue.

    $ sudo apt-get install libpq-dev python-dev postgresql postgresql-contrib

    $ sudo su - postgres
    createdb piremote
    createuser -P piremote
    psql
    GRANT ALL PRIVILEGES ON DATABASE piremote TO piremote
    \q
    logout

Note: the password assigned for the database here has to match the one set in settings.py

## Required Packages

    $ sudo aptitude install python3 python3-pip python3-virtualenv virtualenv nginx coffeescript ruby-sass mpd mpc usbmount git libasound2-dev redis-server
    $ sudo pip3 install django==1.10.5

At least pypugjs 4.1 required (if pypugjs==4.1 installable via pip3, you might use this directly)

    $ sudo pip3 install git+https://github.com/matannoam/pypugjs.git@master
    $ sudo pip3 install django_compressor
    $ sudo pip3 install uwsgi
    $ sudo pip3 install python-mpd2
    $ sudo pip3 install django-websocket-redis
    $ sudo pip3 install mutagen
    $ sudo pip3 install psycopg2

## PiBlaster3 software

    $ cd /opt
    $ sudo chown pi:pi .
    $ git clone https://github.com/ujac81/PiBlaster3.git

Create local settings

    $ cp PiBlaster3/settings_piremote.py.example PiBlaster3/settings_piremote.py

And update settings inside this file.

Make sure DEBUG is not set in your environment, otherwise set DEBUG to FALSE in settings.py.
Also make sure you have correct settings for the SQL database in settings.py.

    $ cd /opt/PiBlaster3
    $ python3 manage.py migrate
    $ python3 manage.py compress --extension='pug'

If any errors occur here, fix them, or nothing will work.

## NGINX

    $ cd /etc/nginx/sites-enabled/
    $ sudo rm default
    $ sudo ln -s /opt/PiBlaster3/conf/site-piblaster
    $ sudo service nginx restart

## UWSGI and Worker

    $ sudo cp /opt/PiBlaster3/conf/piblaster.service /etc/systemd/system
    $ sudo systemctl daemon-reload
    $ sudo systemctl enable piblaster.service

## MPD
Link directories to scan to mpd library and update it.

    $ sudo ln -s /local /var/lib/mpd/music/local
    $ sudo ln -s /media/usb0 /var/lib/mpd/music/usb0
    $ sudo ln -s /media/usb1 /var/lib/mpd/music/usb1
    $ mpc update

# Developer Notes

## Database
PostgreSQL database is used in this project.
For trying out some things and playing with the functionalities of the app, you might revert to sqlite3 database, however concurrent access is not easy for sqlite3.
In theory it should work, but tests on Raspberry Pi showed that the database seems locked the whole time for the worker.
To roll back to sqlite3 change settings.py and exchange all psycopg2 to sqlite3 in the worker modules and check that connect is correct.
Also replace all %s with ? in the SQL commands.

## Create new django project

    $ sudo pip3 install django=x
    See version list
    $ sudo pip3 install django=1.10.5

## Restart service

    $ sudo service piblaster restart

## Run piblaster3 server from command line
To see full debugging output and interact with django server:

    $ sudo service piblaster stop
    $ cd /opt/PiBlaster3
    $ export DEBUG=1
    $ uwsgi --ini conf/piblaster.ini


Connect to http://YOUR_PI_HOST

## PyPugJS templates
All templates are built using the pypugjs(https://github.com/matannoam/pypugjs) interface for pugjs(https://pugjs.org/api/getting-started.html)

Use pypugjs file.pug to check output.

## Coffeescript / Sass
Javascript and CSS files are compiled by django_compress http://django-compressor.readthedocs.io/en/latest/ .
Sass/coffeescript files are handled via COMPRESS_PRECOMPILERS in settings.py.

