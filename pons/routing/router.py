from copy import copy
import pons
from pons.event_log import event_log

HELLO_MSG_SIZE = 42


class Router(object):
    def __init__(self, scan_interval=2.0, capacity=0, apps=None):
        self.scan_interval = scan_interval
        self.peers = []
        self.history = {}
        self.store = []
        self.capacity = capacity
        self.used = 0
        if apps is None:
            apps = []
        self.apps = apps
        self.stats = {
            "rx": 0,
            "tx": 0,
            "failed": 0,
            "delivered": 0,
        }

    def __str__(self):
        return "Router"

    def __repr__(self):
        """Allow seeing value instead of object description"""
        return str(self)

    def log(self, msg):
        print("[ %f ] [%s : %s] ROUTER: %s" % (self.env.now, self.my_id, self, msg))

    def send(self, to_nid: int, msg: pons.Message):
        self.stats["tx"] += 1
        self.netsim.nodes[self.my_id].send(self.netsim, to_nid, msg)
        event_log(
            self.env.now,
            "ROUTER",
            {"event": "TX", "src": self.my_id, "dst": to_nid, "msg": msg.unique_id()},
        )

    def add(self, msg: pons.Message):
        self.store_add(msg)

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
        event_log(
            self.env.now,
            "STORE",
            {
                "event": "ADDED",
                "id": self.my_id,
                "msg": msg.unique_id(),
                "used": self.used,
                "capacity": self.capacity,
            },
        )
        return True

    def store_del(self, msg: pons.Message):
        self.used -= msg.size
        self.store.remove(msg)
        event_log(
            self.env.now,
            "STORE",
            {
                "event": "REMOVED",
                "id": self.my_id,
                "msg": msg.unique_id(),
                "used": self.used,
                "capacity": self.capacity,
            },
        )

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
        # self.log("starting ")
        for app in self.apps:
            # self.log("starting app %s" % app)
            app.start(netsim, my_id)
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
            self.peers.clear()
            self.netsim.nodes[self.my_id].send(
                self.netsim,
                pons.BROADCAST_ADDR,
                pons.Message(
                    "HELLO",
                    self.my_id,
                    pons.BROADCAST_ADDR,
                    HELLO_MSG_SIZE,
                    self.netsim.env.now,
                ),
            )

            yield self.env.timeout(self.scan_interval)

    def _on_tx_failed(self, msg_id: str, remote_id: int):
        self.stats["failed"] += 1
        self.on_tx_failed(msg_id, remote_id)

    def on_tx_failed(self, msg_id: str, remote_id: int):
        pass

    def _on_tx_succeeded(self, msg_id: str, remote_id: int):
        self.on_tx_succeeded(msg_id, remote_id)

    def on_tx_succeeded(self, msg_id: str, remote_id: int):
        pass

    def on_scan_received(self, msg: pons.Message, remote_id: int):
        # self.log("[%s] scan received: %s from %d" %
        #         (self.my_id, msg, remote_id))
        if msg.id == "HELLO" and remote_id not in self.peers:
            self.peers.append(remote_id)
            # self.log("NEW PEER: %d (%s)" % (remote_id, self.peers))
            self.on_peer_discovered(remote_id)
        # elif remote_id in self.peers:
        # self.log("DUP PEER: %d" % remote_id)

    def on_peer_discovered(self, peer_id):
        self.log("peer discovered: %d" % peer_id)

    def _on_msg_received(self, msg: pons.Message, remote_id: int):
        event_log(
            self.env.now,
            "ROUTER",
            {
                "event": "RX",
                "dst": self.my_id,
                "src": remote_id,
                "msg": msg.unique_id(),
            },
        )
        self.stats["rx"] += 1
        # self.log("msg received: %s from %d" % (msg, remote_id))
        self.netsim.routing_stats["relayed"] += 1
        was_known = self.is_msg_known(msg)
        if not was_known:
            self.remember(remote_id, msg)
            msg.hops += 1
            if msg.dst == self.my_id:
                # self.log("msg (%s) arrived on %s" % (msg.id, self.my_id))
                self.stats["delivered"] += 1
                self.netsim.routing_stats["delivered"] += 1
                self.netsim.routing_stats["hops"] += msg.hops
                self.netsim.routing_stats["latency"] += self.env.now - msg.created
                for app in self.apps:
                    if app.service == msg.dst_service:
                        app._on_msg_received(msg)
        else:
            # self.log("msg already known", self.history)
            self.netsim.routing_stats["dups"] += 1
        self.on_msg_received(msg, remote_id, was_known)

    def on_msg_received(self, msg: pons.Message, remote_id: int, was_known: bool):
        self.log("msg received: %s from %d" % (msg, remote_id))

    def remember(self, peer_id, msg: pons.Message):
        if msg.unique_id() not in self.history:
            self.history[msg.unique_id()] = set()

        self.history[msg.unique_id()].add(peer_id)

    def forget(self, peer_id, msg: pons.Message):
        if msg.unique_id() in self.history:
            self.history[msg.unique_id()].remove(peer_id)

    def is_msg_known(self, msg: pons.Message):
        return msg.unique_id() in self.history

    def msg_already_spread(self, msg: pons.Message, remote_id):
        if msg.unique_id() not in self.history:
            return False

        return remote_id in self.history[msg.unique_id()]
