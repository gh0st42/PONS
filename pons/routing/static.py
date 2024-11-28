from typing import List, Optional
from pons.node import Message
from dataclasses import dataclass
from pons.simulation import NetSim
from .router import Router
import networkx as nx
import fnmatch
import random


@dataclass(frozen=True)
class RouteEntry:
    dst: str
    next_hop: int
    hops: Optional[int] = None
    src: Optional[str] = None

    def __str__(self):

        return "RouteEntry(dst=%s, next_hop=%s, hops=%s, src=%s)" % (
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
        shortest_paths_only=False,
        pick_random_next_hop=True,
    ):
        super(StaticRouter, self).__init__(scan_interval, capacity)
        if routes is None:
            routes = []
        self.routes = routes
        self.graph = graph
        self.shortest_paths_only = shortest_paths_only
        self.pick_random_next_hop = pick_random_next_hop

    def start(self, netsim: NetSim, my_id: int):
        super().start(netsim, my_id)
        # get routes from graph to all other nodes
        if not self.routes or self.routes == []:
            next_hop_map = {}
            if self.graph is not None:
                for node in self.graph.nodes:
                    if node != my_id:
                        try:
                            if self.shortest_paths_only:
                                paths = nx.all_shortest_paths(
                                    self.graph, source=my_id, target=node
                                )
                            else:
                                paths = nx.all_simple_paths(
                                    self.graph, source=my_id, target=node
                                )

                            # sort by length
                            paths = sorted(paths, key=lambda x: len(x))

                            for path in paths:
                                next_hop = path[1]
                                if (node, next_hop) in next_hop_map.keys():
                                    if (len(path) - 1) < next_hop_map[(node, next_hop)]:
                                        next_hop_map[(node, next_hop)] = len(path) - 1
                                else:
                                    next_hop_map[(node, next_hop)] = len(path) - 1

                                # self.routes.append(
                                #     RouteEntry(
                                #         dst=node, next_hop=next_hop, hops=len(path) - 1
                                #     )
                                # )
                            # remove duplicates
                            # self.routes = list(set(self.routes))

                        except nx.NetworkXNoPath:
                            pass
            self.routes = [
                RouteEntry(dst=node, next_hop=next_hop, hops=hops)
                for (node, next_hop), hops in next_hop_map.items()
            ]
            self.routes = sorted(self.routes, key=lambda x: x.hops)

        self.log("routes: %s" % self.routes)

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
            self.remember(msg.dst, msg.unique_id())
            # self.store_del(msg)
            return

        next_hops = set()
        # check routing table
        for route in self.routes:
            # self.log("checking route %s" % route)
            next_hop = route.get_next_hop(msg)
            if next_hop is not None:
                # self.log("found route %s for %d" % (route, msg.dst))
                if next_hop in self.peers and not self.msg_already_spread(
                    msg, next_hop
                ):
                    # next_hops.add((next_hop, route.hops))
                    next_hops.add(next_hop)

        # sort by number of hops
        # next_hops = sorted(next_hops, key=lambda x: x[1])
        # next_hops = [next_hop for next_hop, _ in next_hops]
        next_hops = list(set(next_hops))
        # self.log("num routes: %d %s" % (len(next_hops), next_hops))

        # if more than one next hop is available pick a random one
        if len(next_hops) > 0:
            if self.pick_random_next_hop:
                next_hop = random.choice(next_hops)
            else:
                next_hop = next_hops[0]
            # self.log("forwarding to next hop: %d" % next_hop)
            self.netsim.routing_stats["started"] += 1
            # self.netsim.env.process(
            self.send(next_hop, msg)
            # )
            self.remember(next_hop, msg.unique_id())
            # only delete if tx was successful
            # self.store_del(msg)

    def on_tx_succeeded(self, msg_id, remote_id):
        # self.log("msg %s sent to %d" % (msg_id, remote_id))
        self.store_del_by_id(msg_id)

    def on_tx_failed(self, msg_id: str, remote_id: int):
        # self.log("msg %s failed to send to %d" % (msg_id, remote_id))
        pass

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
