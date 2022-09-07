# MQTT - Signal-Cli Gateway

This is a lightweight, single file mqtt to signal-cli gateway written in python. It is assumed that signal-cli is running as a username independent dbus service (without the "-u" option) on the system. The gateway connects to the service and sends messages from signal to the topic.

**This is an PoC and not really intented for production usage.**
```
signal/from/<phonenumberwithout+sign
```
Mqtt publishes to the optic 
```
signal/to/<phonenumberwithout+sign>
```
are send to the corresponding number via signal. For security it has to be set a set of "known numbers" which are allowed to participate to the whole process.

Additionally there is a ```/help``` which atm only shows the command ```/ping``` which sends a publish to the topic
```
signal/ping
```
with the ping requester phone number as payload. The gateway subscribes to this topic too and sends back a chat message ```/pong``` if it receives the sent message back (lightweight application level ping)

Lastly the Gateway will publish a message "1" to
```
signal/<clientId>
```
when connecting and a will message "0" to the same topic, to make the presence visible on mqtt level. This can be prevented by the corresponding parameter

## Installation
* Get signal-cli going on your system and start it as a dbus service (https://github.com/AsamK/signal-cli/wiki/DBus-service)
* make sure the number you want to use is registered and the dbus service can handle it
* Put the files where you need them
    * ```main.py``` wherever you want (has to be executable)
    * ```app.ini``` wherever you want (see example file)
    * ```mqtt-signal-gateway.service``` under ```/etc/systemd/system``` (adjust the paths in the service file to your need)
* enable and start the service
    * ```systemctl enable mqtt-signal-gateway```
    * ```systemctl start mqtt-signal-gateway```

## Dependencies
* signal-cli running as a phone number (user) independent dbus service
* registered phone number via signal-cli
* python3
    * pydbus
    * paho-mqtt
    * GLib

## Special thanks
To AsamK for creating signal-cli (https://github.com/AsamK/signal-cli)