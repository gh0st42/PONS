from .router import Router


class FirstContactRouter(Router):
    def __init__(self, scan_interval=2.0):
        super(FirstContactRouter, self).__init__(scan_interval)
        self.store = []

    def __str__(self):
        return "FirstContactRouter"

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
                    # print("forwarding to peer")
                    self.netsim.routing_stats['started'] += 1
                    # self.netsim.env.process(
                    self.netsim.nodes[self.my_id].send(self.netsim, peer, msg)
                    # )
                    self.remember(peer, msg)
                    self.store_del(msg)
                    return

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        super().on_peer_discovered(peer_id)
        for msg in self.store:
            self.forward(msg)
