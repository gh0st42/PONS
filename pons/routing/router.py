import pons

HELLO_MSG_SIZE = 42


class Router(object):
    def __init__(self, scan_interval=2.0, capacity=0):
        self.scan_interval = scan_interval
        self.peers = []
        self.history = {}
        self.store = []
        self.capacity = capacity
        self.used = 0

    def __str__(self):
        return "Router"

    def __repr__(self):
        """Allow seeing value instead of object description"""
        return str(self)

    def log(self, msg):
        print("[%s : %s] %s" % (self.my_id, self, msg))

    def add(self, msg: pons.Message):
        if self.store_add(msg):
            self.forward(msg)

    def forward(self, msg):
        pass

    def store_add(self, msg: pons.Message):
        if self.capacity > 0 and self.used + msg.size > self.capacity:
            # self.log("store full, no room for msg %s" % msg.id)
            self.store_cleanup()
            self.make_room_for(msg)
            if self.used + msg.size > self.capacity:
                # self.log("store still full, no room for msg %s" % msg.id)
                return False
            # self.log("store cleaned up, made room for msg %s" % msg.id)
        self.store.append(msg)
        self.used += msg.size
        self.netsim.event_manager.on_message_created(self.my_id, msg)
        return True

    def store_del(self, msg: pons.Message):
        self.used -= msg.size
        self.store.remove(msg)
        self.netsim.event_manager.on_message_dropped(self.my_id, msg)

    def store_cleanup(self):
        # [self.store_del(msg)
        # for msg in self.store if msg.is_expired(self.netsim.env.now)]

        for msg in self.store:
            if msg.is_expired(self.netsim.env.now):
                # self.log("removing expired msg %s" % msg.id)
                self.store_del(msg)

    def make_room_for(self, msg: pons.Message):
        if msg.size < self.capacity:
            # self.log("making room for msg %s" % msg.id)
            self.store.sort(key=lambda m: (m.size, m.created))
            while self.used + msg.size > self.capacity:
                # self.log("removing msg %s" % self.store[0].id)
                self.store_del(self.store[0])

    def start(self, netsim: pons.NetSim, my_id: int):
        self.netsim = netsim
        self.env = netsim.env
        self.my_id = my_id
        self.env.process(self.scan())

    def scan(self):
        while True:
            # print("[%s] scanning..." % self.my_id)

            # assume some kind of peer discovery mechanism
            # old_peers = copy(self.peers)
            # self.peers = copy(self.netsim.nodes[self.my_id].neighbors)

            # new_peers = [p for p in self.peers if p not in old_peers]

            # for peer in new_peers:
            #    self.on_peer_discovered(peer)

            # do actual peer discovery with a hello message
            self.netsim.event_manager.on_before_scan(self.my_id)
            self.peers.clear()
            self.netsim.nodes[self.my_id].send(self.netsim, pons.BROADCAST_ADDR, pons.Message(
                "HELLO", self.my_id, pons.BROADCAST_ADDR, HELLO_MSG_SIZE, self.netsim.env.now))

            yield self.env.timeout(self.scan_interval)

    def on_scan_received(self, msg: pons.Message, remote_id: int):
        # self.log("[%s] scan received: %s from %d" %
        #         (self.my_id, msg, remote_id))
        if msg.id == "HELLO" and remote_id not in self.peers:
            self.peers.append(remote_id)
            # self.log("NEW PEER: %d" % remote_id)
            self.on_peer_discovered(remote_id)
        # elif remote_id in self.peers:
            # self.log("DUP PEER: %d" % remote_id)

    def on_peer_discovered(self, peer_id):
        #self.log("peer discovered: %d" % peer_id)
        self.netsim.event_manager.on_peer_discovery(self.my_id, peer_id)

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
                self.netsim.event_manager.on_message_delivered(self.my_id, remote_id, msg)
            else:
                # print("msg not arrived yet", self.my_id)
                self.netsim.event_manager.on_message_received(self.my_id, remote_id, msg)
                self.forward(msg)
        else:
            # print("msg already known", self.history)
            self.netsim.routing_stats['dups'] += 1

    def remember(self, peer_id, msg: pons.Message):
        if msg.id not in self.history:
            self.history[msg.id] = set()

        self.history[msg.id].add(peer_id)

    def is_msg_known(self, msg: pons.Message):
        return msg.id in self.history

    def msg_already_spread(self, msg: pons.Message, remote_id):
        if msg.id not in self.history:
            return False

        return remote_id in self.history[msg.id]
