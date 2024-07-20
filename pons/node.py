from __future__ import annotations

from copy import deepcopy
from typing import List
import pons
import sys

from pons.net.common import BROADCAST_ADDR, NetworkSettings
from simpy.util import start_delayed
import networkx as nx


class Message(object):
    """A message."""

    def __init__(
        self,
        msgid: str,
        src: int,
        dst: int,
        size: int,
        created,
        hops=0,
        ttl=3600,
        src_service: int = 0,
        dst_service: int = 0,
        content={},
        metadata={},
    ):
        self.id = msgid
        self.src = src
        self.dst = dst
        self.size = size
        self.created = created
        self.hops = hops
        self.ttl = ttl
        self.src_service = src_service
        self.dst_service = dst_service
        self.content = content
        self.metadata = metadata

    def __str__(self):
        return "Message(%s, src=%d.%d, dst=%d.%d, size=%d)" % (
            self.id,
            self.src,
            self.src_service,
            self.dst,
            self.dst_service,
            self.size,
        )

    def unique_id(self) -> str:
        return "%s-%d-%d" % (self.id, self.src, self.created)

    def is_expired(self, now):
        # print("is_expired: %d + %d > %d" % (self.created, self.ttl, now))
        return now - self.created > self.ttl


class Node(object):
    """A The ONE movement scenario."""

    def __init__(
        self,
        node_id: int,
        net: List[NetworkSettings] = None,
        router: pons.routing.Router = None,
    ):
        self.id = node_id
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.net = {}
        if net is not None:
            for n in net:
                self.net[n.name] = deepcopy(n)
        self.router = router
        self.neighbors = {}
        self.netsim = None
        for net in self.net.values():
            self.neighbors[net.name] = []

    def __str__(self):
        return "Node(%d, %.02f, %.02f, %.02f)" % (self.id, self.x, self.y, self.z)

    def log(self, msg: str):
        if self.netsim is not None:
            now = self.netsim.env.now
        else:
            now = 0
        print("[ %f ] [%d] NET: %s" % (now, self.id, msg))

    def start(self, netsim: pons.NetSim):
        self.netsim = netsim
        if self.router is not None:
            self.router.start(netsim, self.id)

    def calc_neighbors(self, simtime, nodes: List[Node]):
        for net in self.net.values():
            self.neighbors[net.name] = []
            for node in nodes:
                if node.id != self.id:
                    # print("node %d: %s %s %s" % (node.id, node.net, net.name,  net.has_contact(simtime, self, node)))
                    if net.name in node.net and net.has_contact(simtime, self, node):
                        self.neighbors[net.name].append(node.id)
        # self.log("neighbors: %s @ %f" % (self.neighbors, simtime))

    def add_all_neighbors(self, simtime, nodes: List[Node]):
        for net in self.net.values():
            self.neighbors[net.name] = []
            for node in nodes:
                if node.id != self.id:
                    if net.name in node.net:
                        self.neighbors[net.name].append(node.id)

    def send(self, netsim: pons.NetSim, to_nid: int, msg: Message):
        for net in self.net.values():
            # tx_time = net.tx_time(msg.size)
            if to_nid == BROADCAST_ADDR:
                for nid in self.neighbors[net.name]:
                    if not net.is_lost(netsim.env.now, self.id, nid):
                        try:
                            tx_time = net.tx_time_for_contact(
                                netsim.env.now, self.id, nid, msg.size
                            )
                        except:
                            continue
                        # print("tx_time: %f" % tx_time)
                        receiver = netsim.nodes[nid]
                        netsim.net_stats["tx"] += 1
                        start_delayed(
                            netsim.env, receiver.on_recv(netsim, self.id, msg), tx_time
                        )
                        pons.simulation.event_log(
                            netsim.env.now, "NET", f"TX {self.id} {msg.id} {nid}"
                        )
                    else:
                        # self.log("packet loss: %s to %d" %
                        # (msg.id, to_nid))
                        netsim.net_stats["loss"] += 1
                        pons.simulation.event_log(
                            netsim.env.now, "NET", f"LOST {self.id} {msg.id} {nid}"
                        )
                        # pass
            else:
                if to_nid in self.neighbors[net.name]:
                    if not net.is_lost(netsim.env.now, self.id, to_nid):
                        try:
                            tx_time = net.tx_time_for_contact(
                                netsim.env.now, self.id, to_nid, msg.size
                            )
                            # print("tx_time: %f" % tx_time)
                        except Exception as e:
                            # tx_time = 0.050001
                            continue
                        # self.log("sending msg %s to %d" % (msg, to_nid))
                        receiver = netsim.nodes[to_nid]
                        netsim.net_stats["tx"] += 1
                        pons.simulation.event_log(
                            netsim.env.now, "NET", f"TX {self.id} {msg.id} {to_nid}"
                        )
                        start_delayed(
                            netsim.env, receiver.on_recv(netsim, self.id, msg), tx_time
                        )
                    else:
                        # self.log("packet loss: %s to %d" %
                        # (msg.id, to_nid))
                        netsim.net_stats["loss"] += 1
                        pons.simulation.event_log(
                            netsim.env.now, "NET", f"LOST {self.id} {msg.id} {to_nid}"
                        )
                        # pass

                else:
                    # print("Node %d cannot send msg %s to %d (not in range)" %
                    # (self.id, msg, to_nid))
                    pass

    def on_recv(self, netsim: pons.NetSim, from_nid: int, msg: Message):
        yield netsim.env.timeout(0)
        for net in self.net.values():
            if from_nid in self.neighbors[net.name]:
                # self.log("Node %d received msg %s from %d" % (self.id, msg.id, from_nid))
                netsim.net_stats["rx"] += 1
                netsim.nodes[from_nid].router._on_tx_succeeded(msg.unique_id(), self.id)
                pons.simulation.event_log(
                    netsim.env.now, "NET", f"RX {self.id} {msg.id} {from_nid}"
                )
                if self.router is not None:
                    if msg.id == "HELLO":
                        self.router.on_scan_received(deepcopy(msg), from_nid)
                    else:
                        self.router._on_msg_received(deepcopy(msg), from_nid)
            else:
                # print("Node %d received msg %s from %d (not neighbor)" %
                #      (to_nid, msg, from_nid))
                netsim.net_stats["drop"] += 1
                netsim.nodes[from_nid].router._on_tx_failed(msg.unique_id(), self.id)
                pons.simulation.event_log(
                    netsim.env.now, "NET", f"RX_FAIL {self.id} {msg.id} {from_nid}"
                )


def generate_nodes(
    num_nodes: int,
    offset: int = 0,
    net: List[NetworkSettings] = None,
    router: pons.routing.Router = None,
):
    nodes = []
    if net == None:
        net = []
    for i in range(num_nodes):
        nodes.append(Node(i + offset, net=deepcopy(net), router=deepcopy(router)))
    return nodes


def generate_nodes_from_graph(
    graph: nx.Graph,
    net: List[NetworkSettings] = None,
    router: Router = None,
    contactplan: pons.net.ContactPlan = None,
):
    nodes = []
    if net == None:
        net = []

    if contactplan is not None:
        plan = pons.net.NetworkPlan(deepcopy(graph), contacts=contactplan)

        net.append(
            NetworkSettings(
                "networkplan-%d" % len(graph.nodes()),
                range=0,
                contactplan=plan,
            )
        )
    for i in list(graph.nodes()):
        if (
            (isinstance(i, str) and i.startswith("net_"))
            or str.upper(graph.nodes[i].get("type", "node")) == "SWITCH"
            or str.upper(graph.nodes[i].get("type", "node")) == "NET"
        ):
            continue
        nodes.append(Node(i, net=deepcopy(net), router=deepcopy(router)))

    return nodes
