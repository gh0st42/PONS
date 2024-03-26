#!/bin/sh

if test -f "/tmp/.X1-lock"; then
    rm /tmp/.X1-lock
    rm /tmp/.X11-unix/X1
fi

/usr/bin/tightvncserver -geometry 1920x1080 -depth 24 &
sleep 1
/data/noVNC/utils/novnc_proxy --vnc 127.0.0.1:5901 --listen 0.0.0.0:6080 2>&1 > /tmp/novnc.log &
sleep 4

echo "vnc://127.0.0.1:5901"
echo "http://127.0.0.1:6080/vnc.html"
echo
echo Password: netedit
echo
echo


tail -f /dev/null