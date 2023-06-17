#!/bin/bash

echo "starting broker..."
/etc/init.d/mosquitto start
sleep 10
tail -f /var/log/mosquitto/mosquitto.log
