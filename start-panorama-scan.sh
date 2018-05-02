#!/bin/bash

# put this file in /etc/rc.local so it auto-runs on boot up:
#
# sudo nano /etc/rc.local
# then add this line before the 'exit 0' line:
# sudo bash /home/pi/panorama/start-panorama-scan.sh &
#


# wait a while, hopefully long enough for network to start:
sleep 2m

# check if we can reach google DNS:
nc -zw 1 8.8.8.8 53  >/dev/null 2>&1
online=$?

# NB: raspberry pi time is only updated when connected to a network!
# so we can't use it to time-stamp label our images.
dt=$(date '+%d-%m-%Y--%H:%M:%S')
echo $dt >> /home/pi/panorama/panorama-log.txt

if [ $online -eq 1 ]; then
  # if network down, then auto run our panorama-scan:
  echo "network down" >> /home/pi/panorama/panorama-log.txt
  /usr/bin/python3 /home/pi/panorama/panorama-scan.py /home/pi/panorama/panorama-images
else
  echo "network up" >> /home/pi/panorama/panorama-log.txt
fi
