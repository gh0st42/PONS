from typing import List, Optional
from pons.node import Message
from dataclasses import dataclass
from pons.simulation import NetSim
from .router import Router
import networkx as nx
import fnmatch
import random


@dataclass
class RouteEntry:
    dst: str
    next_hop: int
    hops: Optional[int] = None
    src: Optional[str] = None

    def __str__(self):
        return "RouteEntry(dst=%s, next_hop=%d, hops=%d, src=%s)" % (
            self.dst,
            self.next_hop,
            self.hops,
            self.src,
        )

    def __repr__(self):
        return str(self)

    def get_next_hop(self, msg: Message) -> Optional[int]:
        if isinstance(self.dst, str):
            if fnmatch.fnmatch(str(msg.dst), self.dst):
                return self.next_hop
        elif self.dst == msg.dst:
            return self.next_hop
        else:
            return None


class StaticRouter(Router):
    def __init__(
        self,
        routes: Optional[List[RouteEntry]] = None,
        graph: nx.Graph = None,
        scan_interval=2.0,
        capacity=0,
    ):
        super(StaticRouter, self).__init__(scan_interval, capacity)
        if routes is None:
            routes = []
        self.routes = routes
        self.graph = graph

    def start(self, netsim: NetSim, my_id: int):
        super().start(netsim, my_id)
        # get routes from graph to all other nodes
        if self.graph is not None:
            for node in self.graph.nodes:
                if node != my_id:
                    try:
                        paths = nx.all_shortest_paths(
                            self.graph, source=my_id, target=node
                        )
                        for path in paths:
                            next_hop = path[1]
                            self.routes.append(
                                RouteEntry(
                                    dst=node, next_hop=next_hop, hops=len(path) - 1
                                )
                            )
                    except nx.NetworkXNoPath:
                        pass

    def __str__(self):
        return "StaticRouter"

    def add(self, msg):
        # self.log("adding new msg to store %s" % msg)
        if self.store_add(msg):
            self.forward(msg)

    def forward(self, msg):
        # self.log("%s peers: %s" % (msg, self.peers))
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats["started"] += 1
            # self.netsim.env.process(
            self.send(msg.dst, msg)
            # )
            self.remember(msg.dst, msg)
            self.store_del(msg)
            return

        next_hops = []
        # check routing table
        for route in self.routes:
            # self.log("checking route %s" % route)
            next_hop = route.get_next_hop(msg)
            if next_hop is not None:
                # self.log("found route %s for %d" % (route, msg.dst))
                if next_hop in self.peers and not self.msg_already_spread(
                    msg, next_hop
                ):
                    next_hops.append(next_hop)

        # self.log("num routes: %d %s" % (len(next_hops), next_hops))

        # if more than one next hop is available pick a random one
        if len(next_hops) > 0:
            next_hop = random.choice(next_hops)
            # self.log("forwarding to next hop: %d" % next_hop)
            self.netsim.routing_stats["started"] += 1
            # self.netsim.env.process(
            self.send(next_hop, msg)
            # )
            self.remember(next_hop, msg)
            self.store_del(msg)

    def on_peer_discovered(self, peer_id):
        # self.log("peer discovered: %d" % peer_id)
        for msg in self.store:
            self.forward(msg)

    def on_msg_received(self, msg, remote_id, was_known: bool):
        # self.log("msg received: %s from %d" % (msg, remote_id))
        if not was_known and msg.dst != self.my_id:
            self.store_add(msg)
            # self.log("msg not arrived yet", self.my_id)
            self.forward(msg)
