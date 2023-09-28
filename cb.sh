#!/bin/bash

# Uncomment the following line to run ChiBio in the background
# screen -dmS ChiBio bash -c "gunicorn -b 192.168.7.2:5000 app:application"
# Then, comment out the next line
cd /root/chibio
gunicorn -b 192.168.7.2:5000 app:application --capture-output --log-level info --timeout 0

