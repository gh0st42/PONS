from .router import Router


class DirectDeliveryRouter(Router):
    def __init__(self, scan_interval=2.0, capacity=0):
        super(DirectDeliveryRouter, self).__init__(scan_interval, capacity)

    def __str__(self):
        return "DirectDeliveryRouter"

    def forward(self, msg):
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats['started'] += 1
            # self.netsim.env.process(
            self.netsim.nodes[self.my_id].send(self.netsim, msg.dst, msg)
            # )
            self.remember(msg.dst, msg)
            self.store_del(msg)

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        super().on_peer_discovered(peer_id)
        for msg in self.store:
            self.forward(msg)
