FROM ubuntu:22.04

# Install LXDE and VNC server.
ENV DEBIAN_FRONTEND=noninteractive
RUN \
  apt-get update && \
  apt-get install -y lxde-core lxterminal \
  tightvncserver websockify wmctrl \
  python3 python3-pip git python3-tk python3-networkx && \
  rm -rf /var/lib/apt/lists/*

# HACK: get rid of lxpolkit error in VNC session
RUN mv /usr/bin/lxpolkit /usr/bin/lxpolkit.bak

# deactivate screensaver
RUN sed -i -e "s/@xscreensaver -no-splash/@xset s off\n@xset -dpms\n@xset s noblank\n/g" /etc/xdg/lxsession/LXDE/autostart


# Define working directory.
WORKDIR /data

RUN git clone https://github.com/noVNC/noVNC.git 

RUN mkdir -p /root/.vnc /data/netedit /shared && \
  chmod a+rwx /shared

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/xstartup /root/.vnc/xstartup

RUN touch /root/.Xresources
RUN touch /root/.Xauthority

COPY netedit-tk.py /data/netedit
COPY gui /data/netedit/gui
RUN ln -s /data/netedit/netedit.py /usr/local/bin/netedit

RUN echo "export USER=root" >> /root/.bashrc
ENV USER root
RUN printf "netedit\nnetedit\nn\n" | vncpasswd


# Define default command.
# CMD ["bash"]
ENTRYPOINT ["/entrypoint.sh"]

# Expose ports.
EXPOSE 5901
EXPOSE 6080
