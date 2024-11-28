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
            "aborted": 0,
            "delivered": 0,
            "dropped": 0,
            "removed": 0,
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
        self.remember(to_nid, msg.unique_id())
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

    def store_del(self, msg: pons.Message, dropped: bool = False):
        self.used -= msg.size
        self.store.remove(msg)
        event = "DROPPED" if dropped else "REMOVED"
        event_log(
            self.env.now,
            "STORE",
            {
                "event": event,
                "id": self.my_id,
                "msg": msg.unique_id(),
                "used": self.used,
                "capacity": self.capacity,
            },
        )
        if dropped:
            self.stats["dropped"] += 1
            self.netsim.routing_stats["dropped"] += 1
        else:
            self.stats["removed"] += 1
            self.netsim.routing_stats["removed"] += 1

    def store_del_by_id(self, msg_id: str, dropped: bool = False):
        for msg in self.store:
            if msg.unique_id() == msg_id:
                self.store_del(msg, dropped)
                return

    def store_cleanup(self):
        # [self.store_del(msg)
        # for msg in self.store if msg.is_expired(self.netsim.env.now)]

        for msg in self.store:
            if msg.is_expired(self.netsim.env.now):
                # self.log("removing expired msg %s" % msg.id)
                self.store_del(msg, dropped=True)

    def make_room_for(self, msg: pons.Message):
        if msg.size < self.capacity:
            # self.log("making room for msg %s" % msg.id)
            self.store.sort(key=lambda m: (m.size, m.created))
            while self.used + msg.size > self.capacity:
                # self.log("removing msg %s" % self.store[0].id)
                self.store_del(self.store[0], dropped=True)

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
        self.last_peer_found = self.netsim.env.now

        while True:
            # print("[%s] scanning..." % self.my_id)

            if self.netsim.do_actual_scan:
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
                        metadata={"is_bundle": False},
                    ),
                )
            else:
                # assume some kind of peer discovery mechanism
                self.netsim.nodes[self.my_id].calc_neighbors(
                    self.netsim.env.now, self.netsim.nodes.values()
                )

                old_peers = copy(self.peers)
                peers = set()
                for net in self.netsim.nodes[self.my_id].neighbors.values():
                    peers.update(net)
                self.peers = list(peers)
                # self.peers = copy(self.netsim.nodes[self.my_id].neighbors)

                new_peers = [p for p in self.peers if p not in old_peers]

                for peer in new_peers:
                    self.on_peer_discovered(peer)

                if len(old_peers) == 0 and len(self.peers) > 0:
                    diff = self.netsim.env.now - self.last_peer_found
                    event_log(
                        self.netsim.env.now,
                        "PEERS",
                        {
                            "event": "NO_PEERS_PERIOD",
                            "id": self.my_id,
                            "duration": diff,
                        },
                    )
                elif len(old_peers) > 0 and len(self.peers) == 0:
                    self.last_peer_found = self.netsim.env.now

                    # report period without peers

            yield self.env.timeout(self.scan_interval)

    def _on_tx_failed(self, msg_id: str, remote_id: int):
        self.stats["aborted"] += 1
        self.netsim.routing_stats["aborted"] += 1
        self.forget(remote_id, msg_id)
        self.on_tx_failed(msg_id, remote_id)

    def on_tx_failed(self, msg_id: str, remote_id: int):
        pass

    def _on_tx_succeeded(self, msg_id: str, remote_id: int):
        self.on_tx_succeeded(msg_id, remote_id)

    def on_tx_succeeded(self, msg_id: str, remote_id: int):
        pass

    def on_scan_received(self, msg: pons.Message, remote_id: int):
        # self.log("[%s] scan received: %s from %d" % (self.my_id, msg, remote_id))
        if msg.id == "HELLO" and remote_id not in self.peers:
            self.peers.append(remote_id)
            # self.log("NEW PEER: %d (%s)" % (remote_id, self.peers))
            self.on_peer_discovered(remote_id)
        # elif remote_id in self.peers:
        # self.log("DUP PEER: %d" % remote_id)

    def on_peer_discovered(self, peer_id):
        self.log("peer discovered: %d" % peer_id)

    def _on_pkt_received(self, pkt: pons.Message, remote_id: int):
        if pkt.id == "HELLO":
            self.on_scan_received(pkt, remote_id)
        else:
            self.on_pkt_received(pkt, remote_id)

    def on_pkt_received(self, pkt: pons.Message, remote_id: int):
        pass

    def _on_msg_received(self, msg: pons.Message, remote_id: int):
        event_log(
            self.env.now,
            "ROUTER",
            {
                "event": "RX",
                "at": self.my_id,
                "from": remote_id,
                "src": msg.src,
                "dst": msg.dst,
                "msg": msg.unique_id(),
            },
        )
        self.stats["rx"] += 1
        # self.log("msg received: %s from %d" % (msg, remote_id))
        self.netsim.routing_stats["relayed"] += 1
        was_known = self.is_msg_known(msg)
        if not was_known:
            self.remember(remote_id, msg.unique_id())
            msg.hops += 1
            if msg.dst == self.my_id:
                # self.log("msg (%s) arrived on %s" % (msg.id, self.my_id))
                self.stats["delivered"] += 1
                self.netsim.routing_stats["delivered"] += 1
                self.netsim.routing_stats["hops"] += msg.hops
                self.netsim.routing_stats["latency"] += self.env.now - msg.created
                delivered = False
                for app in self.apps:
                    if app.service == msg.dst_service:
                        app._on_msg_received(msg)
                        delivered = True
                if delivered:
                    event_log(
                        self.env.now,
                        "ROUTER",
                        {
                            "event": "DELIVERED",
                            "src": msg.src,
                            "dst": msg.dst,
                            "msg": msg.unique_id(),
                        },
                    )
                else:
                    event_log(
                        self.env.now,
                        "ROUTER",
                        {
                            "event": "APP_NOT_FOUND",
                            "src": msg.src,
                            "dst": msg.dst,
                            "msg": msg.unique_id(),
                        },
                    )
        else:
            # self.log("msg already known", self.history)
            self.netsim.routing_stats["dups"] += 1
        self.on_msg_received(msg, remote_id, was_known)

    def on_msg_received(self, msg: pons.Message, remote_id: int, was_known: bool):
        self.log("msg received: %s from %d" % (msg, remote_id))

    def remember(self, peer_id, msg_id: str):
        if isinstance(msg_id, pons.Message):
            msg_id = msg_id.unique_id()

        if msg_id not in self.history:
            self.history[msg_id] = set()

        self.history[msg_id].add(peer_id)

    def forget(self, peer_id, msg_id: str):
        if isinstance(msg_id, pons.Message):
            msg_id = msg_id.unique_id()

        if msg_id in self.history:
            self.history[msg_id].remove(peer_id)

    def is_msg_known(self, msg: pons.Message):
        return msg.unique_id() in self.history

    def msg_already_spread(self, msg: pons.Message, remote_id):
        if msg.unique_id() not in self.history:
            return False

        return remote_id in self.history[msg.unique_id()]
