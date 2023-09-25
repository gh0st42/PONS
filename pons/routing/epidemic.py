from .router import Router


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
        super().forward(msg)
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
