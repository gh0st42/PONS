from .router import Router


class EpidemicRouter(Router):
    def __init__(self, scan_interval=2.0, capacity=0, apps=[]):
        super(EpidemicRouter, self).__init__(scan_interval, capacity, apps)

    def __str__(self):
        return "EpidemicRouter"

    def add(self, msg):
        #self.log("adding new msg (%s) to store" % msg.id)
        if self.store_add(msg):
            #self.log("forwarding msg (%s)" % msg.id)
            self.forward(msg)

    def forward(self, msg):
        #self.log("forwarding2 msg (%s)" % msg.id)
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            #self.log("sending %s directly to receiver" % msg.id)
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
        #self.log("new peer discovered: %d" % peer_id)
        for msg in self.store:
            if msg.is_expired(self.netsim.env.now):
                self.store_del(msg)
            else:
                if not self.msg_already_spread(msg, peer_id):
                    self.forward(msg)

    def on_msg_received(self, msg, remote_id):
        # self.log("msg received: %s from %d" % (msg, remote_id))
        self.netsim.routing_stats['relayed'] += 1
        if not self.is_msg_known(msg):
            self.remember(remote_id, msg)
            msg.hops += 1
            if msg.dst == self.my_id:
                #self.log("msg arrived %s" % msg.id)
                self.netsim.routing_stats['delivered'] += 1
                self.netsim.routing_stats['hops'] += msg.hops
                self.netsim.routing_stats['latency'] += self.env.now - msg.created
                for app in self.apps:
                    if app.service == msg.dst_service:
                        app.on_msg_received(msg)
            else:
                self.store_add(msg)
                #self.log("msg (%s) not arrived yet" % (msg.id, self.my_id))
                self.forward(msg)
        else:
            # self.log("msg already known", self.history)
            self.netsim.routing_stats['dups'] += 1
