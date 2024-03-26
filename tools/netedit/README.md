netedit
=======

A simple network topology editor that can export to graphml.
Only requirements are *python3* with *tkinter* and *networkx*.

Besides running `netedit-tk.py` directly, you can also run it in a docker container and an exposed VNC server.

Building the docker image:
```
$ docker build -t gh0st42/netedit .
```

And then run it:
```
$ docker run --rm -it -p 6080:6080 -p 5901:5901 --name netedit -v $(pwd):/shared gh0st42/netedit
vnc://127.0.0.1:5901
http://127.0.0.1:6080/vnc.html
Password: netedit
xauth:  file /root/.Xauthority does not exist
WebSocket server settings:
  - Listen on :6080
  - Web server. Web root: /data/noVNC
  - No SSL/TLS support (no cert file)
  - proxying from :6080 to localhost:5901

New 'X' desktop is bac8b6ec8acd:1

Starting applications specified in /root/.vnc/xstartup
Log file is /root/.vnc/bac8b6ec8acd:1.log

```