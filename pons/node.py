from __future__ import annotations

import math
from copy import deepcopy
import pons
import random

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pons.routing

BROADCAST_ADDR = 0xFFFF


class NetworkSettings(object):
    """A network settings.
    """

    def __init__(self, name, range, bandwidth=54000000, loss=0.0, delay=0.05):
        self.name = name
        self.bandwidth = bandwidth
        self.loss = loss
        self.delay = delay
        self.range = range
        self.range_sq = range * range

    def __str__(self):
        return "NetworkSettings(%s, %.02f, %.02f, %.02f, %.02f)" % (self.name, self.range, self.bandwidth, self.loss, self.delay)

    def tx_time(self, size):
        return size / self.bandwidth + self.delay

    def is_lost(self):
        return random.random() < self.loss

    def is_in_range(self, src: Node, dst: Node):
        dx = src.x - dst.x
        dy = src.y - dst.y

        # sqrt is expensive, so we use the square of the distance
        # dist = math.sqrt(dx * dx + dy * dy)
        dist = dx * dx + dy * dy
        return dist <= self.range_sq


class Message(object):
    """A message.
    """

    def __init__(self, msgid: str, src: int, dst: int, size: int, created, hops=0, ttl=3600*24, content={}, metadata={}):
        self.id = msgid
        self.src = src
        self.dst = dst
        self.size = size
        self.created = created
        self.hops = hops
        self.ttl = ttl
        self.content = content
        self.metadata = metadata

    def __str__(self):
        return "Message(%s, %d, %d, %d)" % (self.id, self.src, self.dst, self.size)

    def is_expired(self, now):
        return self.created + self.ttl > now


class Node(object):
    """A The ONE movement scenario.
    """

    def __init__(self, node_id: int, net: List[NetworkSettings] = None, router: pons.routing.Router = None):
        self.id = node_id
        self.x = 0.0
        self.y = 0.0
        self.net = {}
        if net is not None:
            for n in net:
                self.net[n.name] = deepcopy(n)
        self.router = router
        self.neighbors = {}
        for net in self.net.values():
            self.neighbors[net.name] = []

    def __str__(self):
        return "Node(%d, %.02f, %.02f)" % (self.id, self.x, self.y)

    def log(self, msg: str):
        print("[%d]: %s" % (self.id, msg))

    def start(self, netsim: pons.NetSim):
        self.netsim = netsim
        if self.router is not None:
            self.router.start(netsim, self.id)

    def calc_neighbors(self, nodes):
        for net in self.net.values():
            self.neighbors[net.name] = []
            for node in nodes:
                if node.id != self.id:
                    if net.name in node.net and net.is_in_range(self, node):
                        self.neighbors[net.name].append(node.id)
        # self.log("neighbors: %s" % (self.neighbors))

    def send(self, netsim: pons.NetSim, to_nid: int, msg: Message):
        for net in self.net.values():
            if not net.is_lost():
                tx_time = net.tx_time(msg.size)
                if to_nid == BROADCAST_ADDR:
                    for nid in self.neighbors[net.name]:
                        receiver = netsim.nodes[nid]
                        netsim.net_stats["tx"] += 1
                        pons.delayed_execution(netsim.env, tx_time,
                                               receiver.on_recv(netsim, self.id, msg))
                else:
                    if to_nid in self.neighbors[net.name]:
                        # self.log("sending msg %s to %d" % (msg, to_nid))
                        receiver = netsim.nodes[to_nid]
                        netsim.net_stats["tx"] += 1
                        pons.delayed_execution(netsim.env, tx_time,
                                               receiver.on_recv(netsim, self.id, msg))
                    else:
                        # print("Node %d cannot send msg %s to %d (not in range)" %
                        # (self.id, msg, to_nid))
                        pass
            else:
                # self.log("packet loss: %s to %d" %
                # (msg.id, to_nid))
                netsim.net_stats["loss"] += 1
                # pass

    def on_recv(self, netsim: pons.NetSim, from_nid: int, msg: Message):
        for net in self.net.values():
            if from_nid in self.neighbors[net.name]:
                # print("Node %d received msg %s from %d" % (to_nid, msg, from_nid))
                netsim.net_stats["rx"] += 1
                if self.router is not None:
                    if msg.id == "HELLO":
                        self.router.on_scan_received(deepcopy(msg), from_nid)
                    else:
                        self.router.on_msg_received(deepcopy(msg), from_nid)
            else:
                # print("Node %d received msg %s from %d (not neighbor)" %
                #      (to_nid, msg, from_nid))
                netsim.net_stats["drop"] += 1


def generate_nodes(num_nodes: int, offset: int = 0, net: List[NetworkSettings] = None, router: pons.routing.Router = None):
    nodes = []
    if net == None:
        net = []
    for i in range(num_nodes):
        nodes.append(Node(i + offset, net=deepcopy(net),
                     router=deepcopy(router)))
    return nodes
