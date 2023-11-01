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
        msg.metadata['copies'] = self.copies
        super().add(msg)

    def forward(self, msg):
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats['started'] += 1
            # self.netsim.env.process(
            self.netsim.nodes[self.my_id].send(self.netsim, msg.dst, msg)
            # )
            self.remember(msg.dst, msg)
            self.store_del(msg)
        elif msg.metadata['copies'] > 1:
            # self.log("broadcasting to peers ", self.peers)
            for peer in self.peers:
                if not self.msg_already_spread(msg, peer) and msg.metadata['copies'] > 1:
                    # print("forwarding to peer")
                    outmsg = copy.deepcopy(msg)
                    self.netsim.routing_stats['started'] += 1
                    if self.binary:
                        outmsg.metadata['copies'] = math.ceil(
                            msg.metadata['copies'] / 2)
                        msg.metadata['copies'] = math.floor(
                            msg.metadata['copies'] / 2)
                    else:
                        outmsg.metadata['copies'] = 1
                        msg.metadata['copies'] -= 1

                    # self.netsim.env.process(
                    self.netsim.nodes[self.my_id].send(
                        self.netsim, peer, outmsg)
                    # )
                    self.remember(peer, msg)

    def on_peer_discovered(self, peer_id):
        super().on_peer_discovered(peer_id)
        for msg in self.store:
            self.forward(msg)
