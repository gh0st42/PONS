from .router import Router


class DirectDeliveryRouter(Router):
    def __init__(self, scan_interval=2.0, capacity=0):
        super(DirectDeliveryRouter, self).__init__(scan_interval, capacity)

    def __str__(self):
        return "DirectDeliveryRouter"

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
            self.remember(msg.dst, msg)
            self.store_del(msg)

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
                # self.log("msg arrived", self.my_id)
                self.netsim.routing_stats["delivered"] += 1
                self.netsim.routing_stats["hops"] += msg.hops
                self.netsim.routing_stats["latency"] += self.env.now - msg.created
                for app in self.apps:
                    if app.service == msg.dst_service:
                        app.on_msg_received(msg)
            else:
                self.store_add(msg)
                # self.log("msg not arrived yet", self.my_id)
                self.forward(msg)
        else:
            # self.log("msg already known", self.history)
            self.netsim.routing_stats["dups"] += 1
