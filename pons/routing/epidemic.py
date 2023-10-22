from .router import Router
import pons


class EpidemicRouter(Router):
    def __init__(self, scan_interval=2.0, capacity=0):
        super(EpidemicRouter, self).__init__(scan_interval, capacity)

    def __str__(self):
        return "EpidemicRouter"

    def add(self, msg):
        # self.log("adding new msg to store")
        if self.store_add(msg):
            self.forward(msg)

    def forward(self, msg):
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats['started'] += 1
            # self.netsim.env.process(
            self.netsim.nodes[self.my_id].send(self.netsim, msg.dst, msg)
            # )
            self.remember(msg.dst, msg)
            self.store_del(msg)
        else:
            # self.log("broadcasting to peers ", self.peers)
            for peer in self.peers:
                if not self.msg_already_spread(msg, peer):
                    # self.log("forwarding to peer")
                    self.netsim.routing_stats['started'] += 1
                    # self.netsim.env.process(
                    self.netsim.nodes[self.my_id].send(self.netsim, peer, msg)
                    # )
                    self.remember(peer, msg)

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        for msg in self.store:
            if msg.is_expired(self.netsim.env.now):
                self.store_del(msg)
            else:
                self.forward(msg)

    def on_msg_received(self, msg: pons.Message, remote_id: int):
        self.netsim.routing_stats['relayed'] += 1
        if not self.is_msg_known(msg):
            self.remember(remote_id, msg)
            msg.hops += 1
            self.store_add(msg)
            if msg.dst == self.my_id:
                # print("msg arrived", self.my_id)
                self.netsim.routing_stats['delivered'] += 1
                self.netsim.routing_stats['hops'] += msg.hops
                self.netsim.routing_stats['latency'] += self.env.now - msg.created
            else:
                # print("msg not arrived yet", self.my_id)
                self.forward(msg)
        else:
            # print("msg already known", self.history)
            self.netsim.routing_stats['dups'] += 1