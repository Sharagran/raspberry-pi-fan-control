#!/bin/bash

if [[ $UID != 0 ]]; then
    echo "Please run this script with sudo:"
    echo "sudo $0 $*"
    exit 1
fi

# check if pip3 is installed
if ! pip3 -V &> /dev/null
then
    echo "pip3 could not be found"
    exit 1
fi

# install dependencies
pip3 install getopt RPi.GPIO

# copy files
mkdir /opt/my_scripts
cp fan-controller.py /opt/my_scripts/
cp fan-controller.service /etc/systemd/system/

# start service
systemctl start fan-controller.service
systemctl enable fan-controller.service
