#!/bin/sh

/usr/bin/tightvncserver -geometry 1920x1080 -depth 24 &

/data/noVNC/utils/novnc_proxy --vnc localhost:5901 2>&1 > /tmp/novnc.log &

echo "vnc://127.0.0.1:5901"
echo "http://127.0.0.1:6080/vnc.html"
echo
echo Password: netedit
echo
echo

tail -f /dev/null