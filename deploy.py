import os

stream = os.popen("ip addr show usb0 | grep -Po 'inet \K[\d.]+'")

ip_addr = stream.read()
ip_addr = ip_addr.rstrip('\r\n')
with open('cb.sh','w') as f:
    f.write('gunicorn -b %s:5000 app:application\r\n'%ip_addr)
