from copy import copy
import random
import pons
from pons.event_log import event_log
import socket
import json
import threading

from . import App


class UdpGatewayApp(App):
    def __init__(
        self,
        service: int = 7,
        udp_out: tuple[str, int] | None = None,
        udp_in: int | None = None,
    ):
        super().__init__(service)
        self.msgs_sent = 0
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}
        self.udp_out = udp_out
        self.udp_in = udp_in

    def log(self, msg):
        print(
            "[ %f ] [%s.%d] APP: %s"
            % (self.netsim.env.now, self.my_id, self.service, msg)
        )

    def __str__(self):
        return "UdpGatewayApp (%d, %d, >%s, <%d)" % (
            self.my_id,
            self.service,
            self.udp_out,
            self.udp_in,
        )

    def start(self, netsim: pons.NetSim, my_id: int):
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        # self.netsim.env.process(self.run())
        if self.udp_in is not None:
            # spawn a daemon thread to listen for UDP messages

            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def on_msg_received(self, msg: pons.Message):
        # print("message received in UDP app: %s" % msg)
        if self.udp_out:
            self.log(
                "sending %s as UDP message to %s" % (msg.unique_id(), self.udp_out)
            )
            # Here you would send the message via UDP, e.g., using a socket
            # For simulation purposes, we just log it
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(msg.content.encode(), self.udp_out)
            finally:
                sock.close()

    def run(self):
        if self.udp_in is None:
            return
        self.log("binding to UDP port %d" % self.udp_in)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.udp_in))
        # set the socket to non-blocking mode
        # sock.setblocking(False)
        while True:
            print("waiting for UDP packets on port %d" % self.udp_in)
            try:
                pkt, addr = sock.recvfrom(65535)
                print(pkt)
                pkt_in = json.loads(pkt.decode())
                self.log("received UDP packet from %s: %s" % (addr, pkt_in))
                print("received UDP packet from %s: %s" % (addr, pkt_in))
                dst_id, dst_service = pkt_in["dst"].split(":")[1].split(".")
                dst_id = int(dst_id)
                dst_service = int(dst_service)
                msg = pons.Message(
                    "UDP-%d-%d" % (self.my_id, self.msgs_sent),
                    self.my_id,
                    dst_id,
                    len(pkt_in["content"]),
                    created=self.netsim.env.now,
                    content=pkt_in["content"],
                    ttl=pkt_in.get("ttl", 3600),
                    src_service=self.service,
                    dst_service=dst_service,
                )
                print("Created message: %s" % msg)
                self.send(msg)
                self.msgs_sent += 1
            except Exception as e:
                self.log("error receiving UDP packet: %s" % e)
                continue

            # yield self.netsim.env.timeout(0.1)  # simulate processing time
