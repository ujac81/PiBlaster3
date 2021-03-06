# PiBlaster3

3rd version of PiBlaster software -- access point / web version

Install instructions -- updated 2016/12/16

# Set up Raspberry Pi
Install latest raspbian, like told on the website.
After first boot run

    $ sudo raspi-config

Enable ssh, set locale, set timezone, disable waiting for network at boot.

## Hifiberry AMP
If using PiBlaster with hifiberry amp, follow instructions on the website: https://www.hifiberry.com/build/documentation/configuring-linux-3-18-x/
Don't forget to set up the equalizer if desired: https://support.hifiberry.com/hc/en-us/articles/205311292-Adding-equalization-using-alsaeq

## Access Point Mode
To access the PiBlaster 3 interface via WiFi, you can either use the onboard WiFi device which comes with newer versions of raspberry Pi or you can attach a usb WiFi-dongle.
If using another dongle, please check if you need to set wlan0 or wlan1 here.

**Note:** other devices require other drivers for hostapd.conf!!! There are some dongles which require drivers that are not shipped with the default version of hostapd. You will have to find another distribution of hostapd or patch the sources or whatever...

Example set for net 192.168.207.0

**Note:** settings configured for wlan0 -- if you have no raspi model #3, you might want to switch to wlan0.

    $ sudo apt install hostapd dnsmasq

Prevent dhcpd on wlan interface. At the bottom of /etc/dhcpcd.conf add

    denyinterfaces wlan0

/etc/network/interfaces

    iface wlan0 inet static
      address 192.168.207.1
      network 192.168.207.0
      netmask 255.255.255.0
      broadcast 192.168.207.255

Use hostapd.conf from PiBlaster3 installation to /etc/default/hostapd make sure WPA passphrase changes via piadmin are valid.

    DAEMON_CONF="/opt/PiBlaster3/conf/hostapd.conf"

/etc/hosts

    192.168.207.1 blaster.local blaster

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

    $ sudo systemctl enable nginx hostapd
    $ sudo systemctl enable nginx dnsmasq

## Reverse Proxy
Nginx will be used as revere proxy and delivery of mp3 files.
Configuration will be done, when PiBlaster3 is installed.

    $ sudo apt install nginx
    $ sudo systemctl enable nginx

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

    $ sudo apt install python3 python3-pip python3-virtualenv virtualenv nginx coffeescript ruby-sass mpd mpc usbmount git libasound2-dev redis-server
    $ sudo pip3 install wheel django==1.10.5

At least pypugjs 4.1 required (if pypugjs==4.1 installable via pip3, you might use this directly)

    $ sudo pip3 install django_compressor uwsgi python-mpd2 django-websocket-redis mutagen psycopg2 pypugjs

## PiBlaster3 software

    $ cd /opt
    $ sudo chown pi:pi .
    $ git clone https://github.com/ujac81/PiBlaster3.git

Create local settings

    $ cd /opt/PiBlaster3
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

## Restart service

    $ sudo service piblaster restart

## Run piblaster3 server from command line
To see full debugging output and interact with django server:

    $ sudo service piblaster stop
    $ cd /opt/PiBlaster3
    $ export DEBUG=1
    $ export PROFILE=1
    $ uwsgi --ini conf/piblaster.ini


Connect to http://YOUR_PI_HOST

## PyPugJS templates
All templates are built using the pypugjs(https://github.com/matannoam/pypugjs) interface for pugjs(https://pugjs.org/api/getting-started.html)

Use pypugjs file.pug to check output.

## Coffeescript / Sass
Javascript and CSS files are compiled by django_compress http://django-compressor.readthedocs.io/en/latest/ .
Sass/coffeescript files are handled via COMPRESS_PRECOMPILERS in settings.py.

## Upgrading

### Python Packages
If using virtual environment use

   # python3 -m venv --upgrade /path/to/venv

Upgrade all python packages installed via pip

    # pip3 install --force pip
    # pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U
    # pip3 list --outdated --format=legacy | grep -v '^\-e' | cut -d ' ' -f 1 | xargs -n1 pip3 install -U
    
**NOTE:** If you used sudo to install pip packages, you might need sudo again here before the pip3 commands.
     
### PostgreSQL
Upgrade PostgreSQL databases to new version (after distupgrade or such).

    Assumption: new psql version installed by dist upgrade, old running.
    $ sudo service postgres stop
    $ sudo su - postgres
    $ cd
    Create Backup
    $ pg_dumpall > backup.sql
    Remove newly created cluster for the upgraded version (NOT YOUR OLD ONE)
    $ pg_dropcluster 9.6 main
    $ pg_upgradecluster 9.5 main
    $ pg_dropcluster 9.5 main
    $ logout
    $ sudo apt remove postgresql-9.5 postgresql-client-9.5 postgresql-contrib-9.5
    $ sudo systemctl daemon-reload
    $ sudo service postgresql start

## Testing

### Create test database

    $ sudo su - postgres
    createdb test_piremote
    psql
    GRANT ALL PRIVILEGES ON DATABASE test_piremote TO piremote;
    ALTER DATABASE test_piremote OWNER TO piremote;
    ALTER USER piremote CREATEDB;
    \q
    logout

### Run tests
Make sure DEBUG is not set in env!

    $ ./manage.py compress --extension=pug
    $ ./manage.py test

## Migrations

Modify piremote/models.py (add/remove data fields, add classes and so on),
then create migration and apply it to database:

    $ ./manage.py makemigrations
    $ ./manage.py migrate

Make sure you generate a meaningful default value when adding fields.
If changes in Rating model made, you might use rating_scanner to seed the missing fields.

## Misc

### Count code lines

    $ sudo apt install cloc
    $ cd PIBLASTER3_MAIN_FOLDER
    $ cloc --counted=counts.txt --exclude-dir=CACHE,vendor --exclude-lang=JavaScript  piadmin PiBlaster3 piremote workers

Check counts.txt file for files taken into account.
