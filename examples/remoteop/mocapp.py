import random
import sys
import pathlib
import math
import threading
import json

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
print(SCRIPT_DIR)
try:
    import pons
except ImportError:
    print(SCRIPT_DIR.parent.parent.resolve())
    sys.path.append(str(SCRIPT_DIR.parent.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

from pons.apps.app import App
from pons.event_log import event_log
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


# Supported rover commands:
# - forward: move forward at a given speed for a given time
# - turn: turn to a given angle
# - cancel: cancel the current movement
# - clear: clear the command queue
# - sleep: sleep for a given time

tmbuf = []
tmhistory = []
from copy import copy


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # first we need to parse it
        parsed = urlparse(self.path)
        # get the query string
        query_string = parsed.query
        # get the request path, this new path does not have the query string
        path = parsed.path
        global tmbuf
        global tmhistory

        if path == "/read/tmbuf":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            data = "\n".join(tmbuf)
            self.wfile.write(data.encode("utf-8"))
            tmhistory.extend(copy(tmbuf))
            tmbuf = []
            return
        elif path == "/read/tmhistory":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            data = "\n".join(tmhistory)
            self.wfile.write(data.encode("utf-8"))
            return
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello, world: " + path.encode("utf-8"))


class MocApp(App):
    def __init__(
        self,
        dst: int,
        service: int = 7,
        dst_service: int = 7,
        http_port: int = 18080,
        ttl: int = 3600,
    ):
        super().__init__(service)
        self.msgs_sent = 0
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}
        self.http_port = http_port
        self.ttl = ttl
        self.dst = dst
        self.dst_service = dst_service

    def __str__(self):
        return "MocApp (%d, %d)" % (self.my_id, self.service)

    def log(self, msg):
        print(
            "[ %f ] [%s.%d] APP: %s"
            % (self.netsim.env.now, self.my_id, self.service, msg)
        )

    def run_server(self):
        import http.server

        # handler = http.server.SimpleHTTPRequestHandler
        self.handler = HttpHandler
        self.httpd = socketserver.TCPServer(("", self.http_port), self.handler)
        self.log(f"serving at port {self.http_port}")
        self.httpd.serve_forever()

    def start(self, netsim: pons.NetSim, my_id: int):
        # self.rover = Rover("rover1", x=50, y=50, direction=0, netsim=netsim)
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        # self.rover.start(netsim, my_id)
        # self.netsim.env.process(self.run())

        server_thread = threading.Thread(target=self.run_server, args=())
        server_thread.daemon = True
        server_thread.start()

    def on_msg_received(self, msg: pons.Message):
        global tmbuf
        self.log("TM received: %s" % (msg.id))
        self.msgs_received += 1
        now = self.netsim.env.now
        self.log(
            "%s received from node %s with %d bytes in %fs"
            % (msg.id, msg.src, msg.size, now - msg.created)
        )
        tmbuf.append(f"{now} {msg.src} {msg.unique_id()} {msg.size}")
        self.msgs_received += 1

    def run(self):
        pass
