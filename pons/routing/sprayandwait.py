from .router import Router

import copy
import math


class SprayAndWaitRouter(Router):
    def __init__(
        self, copies=7, binary=False, scan_interval=2.0, capacity=0, apps=None
    ):
        super(SprayAndWaitRouter, self).__init__(scan_interval, capacity, apps)
        self.store = []
        self.copies = copies
        self.binary = binary

    def __str__(self):
        if self.binary:
            return "BinarySprayAndWaitRouter_%d" % self.copies
        return "SprayAndWaitRouter_%d" % self.copies

    def add(self, msg):
        # print("adding new msg to store")
        msg.metadata["copies"] = self.copies
        if self.store_add(msg):
            self.forward(msg)

    def forward(self, msg):
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats["started"] += 1
            # self.netsim.env.process(
            self.send(msg.dst, msg)
            # )
            self.remember(msg.dst, msg.unique_id())
            self.store_del(msg)
        elif msg.metadata["copies"] > 1:
            # self.log("broadcasting to peers ", self.peers)
            for peer in self.peers:
                if (
                    not self.msg_already_spread(msg, peer)
                    and msg.metadata["copies"] > 1
                ):
                    # print("forwarding to peer")
                    outmsg = copy.deepcopy(msg)
                    self.netsim.routing_stats["started"] += 1
                    if self.binary:
                        outmsg.metadata["copies"] = math.ceil(
                            msg.metadata["copies"] / 2
                        )
                        msg.metadata["copies"] = math.floor(msg.metadata["copies"] / 2)
                    else:
                        outmsg.metadata["copies"] = 1
                        msg.metadata["copies"] -= 1

                    # self.netsim.env.process(
                    self.send(peer, outmsg)
                    # )
                    self.remember(peer, msg.unique_id())

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        for msg in self.store:
            self.forward(msg)

    def on_msg_received(self, msg, remote_id, was_known):
        # self.log("msg received: %s from %d" % (msg, remote_id))
        if not was_known and msg.dst != self.my_id:
            self.store_add(msg)
            # self.log("msg not arrived yet", self.my_id)
            self.forward(msg)
