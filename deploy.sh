#!/bin/bash

IP=ip addr show usb0 | grep -Po 'inet \K[\d.]+'

echo "gunicorn -b ${IP}:5000 app:application" | tee cb.sh