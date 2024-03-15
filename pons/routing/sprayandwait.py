from .router import Router

import copy
import math


class SprayAndWaitRouter(Router):
    def __init__(self, copies=7, binary=False, scan_interval=2.0):
        super(SprayAndWaitRouter, self).__init__(scan_interval)
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
            self.remember(msg.dst, msg)
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
                    self.remember(peer, msg)

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        for msg in self.store:
            self.forward(msg)

    def on_msg_received(self, msg, remote_id):
        # self.log("msg received: %s from %d" % (msg, remote_id))
        self.netsim.routing_stats["relayed"] += 1
        if not self.is_msg_known(msg):
            self.remember(remote_id, msg)
            msg.hops += 1
            if msg.dst == self.my_id:
                # print("msg arrived", self.my_id)
                self.netsim.routing_stats["delivered"] += 1
                self.netsim.routing_stats["hops"] += msg.hops
                self.netsim.routing_stats["latency"] += self.env.now - msg.created
                for app in self.apps:
                    if app.service == msg.dst_service:
                        app.on_msg_received(msg)
            else:
                self.store_add(msg)
                # print("msg not arrived yet", self.my_id)
                self.forward(msg)
        else:
            # print("msg already known", self.history)
            self.netsim.routing_stats["dups"] += 1
