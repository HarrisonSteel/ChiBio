#!/bin/bash

# Uncomment the following line to run ChiBio in the background
# screen -dmS ChiBio bash -c "gunicorn -b 192.168.178.116:5000 app:application"
# Then, comment out the next line
cd /root/chibio
gunicorn -b 192.168.178.116:5000 app:application --capture-output --log-level info --timeout 0

