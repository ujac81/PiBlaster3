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
Use nginx to forward :5000 flask web server to port 80.
Use nginx to deliver mp3 files directly.

    $ sudo aptitude install nginx

/etc/nginx/sites-enabled/default

    server {
            listen 80;
            server_name pi.blaster;
            access_log off;
            location / {
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                    proxy_set_header Host $http_host;
                    proxy_set_header X-NginX-Proxy true;
                    proxy_pass http://127.0.0.1:5000/;
                    proxy_redirect off;
            }
    }

Enable nginx proxy at boot

    $ sudo update-rc.d nginx enable

## Required Packages

    $ sudo aptitude install python3-flask ipython3 python3-pip
    $ sudo pip3 install flask-socketio
    $ sudo pip3 install flask-bootstrap

