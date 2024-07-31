from .router import Router


class FirstContactRouter(Router):
    def __init__(self, scan_interval=2.0, capacity=0, apps=None):
        super(FirstContactRouter, self).__init__(scan_interval, capacity, apps)
        self.store = []

    def __str__(self):
        return "FirstContactRouter"

    def add(self, msg):
        # print("adding new msg to store")
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
        else:
            # self.log("broadcasting to peers ", self.peers)
            for peer in self.peers:
                if not self.msg_already_spread(msg, peer):
                    # print("forwarding to peer")
                    self.netsim.routing_stats["started"] += 1
                    # self.netsim.env.process(
                    self.send(peer, msg)
                    # )
                    self.remember(peer, msg.unique_id())
                    self.store_del(msg)
                    return

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
