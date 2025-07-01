from __future__ import annotations

from copy import deepcopy
from typing import List
import pons
from pons.message import Message

from pons.net.common import BROADCAST_ADDR, NetworkSettings
from simpy.util import start_delayed
import networkx as nx
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class Node(object):
    """A The ONE movement scenario."""

    netsim: None | pons.NetSim

    def __init__(
        self,
        node_id: int,
        node_name: str = "",
        net: list[NetworkSettings] | None = None,
        router: pons.routing.Router | None = None,
    ):
        self.node_id = node_id
        self.name = node_name
        if self.name == "":
            self.name = "n%d" % self.node_id
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
        for n in self.net.values():
            self.neighbors[n.name] = []

    def __str__(self):
        return "Node(%d (%s), %.02f, %.02f, %.02f)" % (
            self.node_id,
            self.name,
            self.x,
            self.y,
            self.z,
        )

    def log(self, msg: str):
        if self.netsim is not None:
            now = self.netsim.env.now
        else:
            now = 0
        logger.info("[ %f ] [ %d | %s ] NET: %s" % (now, self.node_id, self.name, msg))

    def start(self, netsim: pons.NetSim):
        self.netsim = netsim
        if self.router is not None:
            self.router.start(netsim, self.node_id)

    def calc_neighbors(self, simtime, nodes: List[Node]):
        for net in self.net.values():
            self.neighbors[net.name] = []
            for node in nodes:
                if node.node_id != self.node_id:
                    # print("node %d: %s %s %s" % (node.id, node.net, net.name,  net.has_contact(simtime, self, node)))
                    if net.name in node.net and net.has_contact(simtime, self, node):
                        self.neighbors[net.name].append(node.node_id)
        # self.log("neighbors: %s @ %f" % (self.neighbors, simtime))

    def add_all_neighbors(self, simtime, nodes: List[Node]):
        for net in self.net.values():
            self.neighbors[net.name] = []
            for node in nodes:
                if node.node_id != self.node_id:
                    if net.name in node.net:
                        self.neighbors[net.name].append(node.node_id)

    def send(self, netsim: pons.NetSim, to_nid: int, msg: Message):
        for net in self.net.values():
            # tx_time = net.tx_time(msg.size)
            if to_nid == BROADCAST_ADDR:
                for nid in self.neighbors[net.name]:
                    if not net.is_lost(netsim.env.now, self.node_id, nid):
                        try:
                            tx_time = net.tx_time_for_contact(
                                netsim.env.now, self.node_id, nid, msg.size
                            )
                        except:
                            logger.warning(
                                "Tx Time Error (%s %s): %s" % (self.node_id, to_nid, e)
                            )

                            continue
                        # print("tx_time: %f" % tx_time)
                        receiver = netsim.nodes[nid]
                        netsim.net_stats["tx"] += 1
                        start_delayed(
                            netsim.env,
                            receiver.on_recv(netsim, self.node_id, msg),
                            tx_time,
                        )
                        pons.simulation.event_log(
                            netsim.env.now,
                            "NET",
                            {
                                "event": "TX",
                                "id": self.node_id,
                                "msg": msg.unique_id(),
                                "to": nid,
                            },
                        )
                    else:
                        # self.log("packet loss: %s to %d" %
                        # (msg.id, to_nid))
                        netsim.net_stats["loss"] += 1
                        pons.simulation.event_log(
                            netsim.env.now,
                            "NET",
                            {
                                "event": "LOST",
                                "id": self.node_id,
                                "msg": msg.unique_id(),
                                "to": nid,
                            },
                        )
                        # pass
            else:
                if to_nid in self.neighbors[net.name]:
                    if not net.is_lost(netsim.env.now, self.node_id, to_nid):
                        try:
                            tx_time = net.tx_time_for_contact(
                                netsim.env.now, self.node_id, to_nid, msg.size
                            )
                            # logger.debug("tx_time: %f" % tx_time)
                        except Exception as e:
                            logger.warning(
                                "Tx Time Error (%s %s): %s" % (self.node_id, to_nid, e)
                            )
                            # tx_time = 0.050001
                            continue
                        # self.log("sending msg %s to %d" % (msg, to_nid))
                        receiver = netsim.nodes[to_nid]
                        netsim.net_stats["tx"] += 1
                        pons.simulation.event_log(
                            netsim.env.now,
                            "NET",
                            {
                                "event": "TX",
                                "id": self.node_id,
                                "msg": msg.unique_id(),
                                "to": to_nid,
                            },
                        )
                        start_delayed(
                            netsim.env,
                            receiver.on_recv(netsim, self.node_id, msg),
                            tx_time,
                        )
                    else:
                        # self.log("packet loss: %s to %d" %
                        # (msg.id, to_nid))
                        netsim.net_stats["loss"] += 1
                        pons.simulation.event_log(
                            netsim.env.now,
                            "NET",
                            {
                                "event": "LOST",
                                "id": self.node_id,
                                "msg": msg.unique_id(),
                                "to": to_nid,
                            },
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
                netsim.nodes[from_nid].router._on_tx_succeeded(
                    msg.unique_id(), self.node_id
                )
                pons.simulation.event_log(
                    netsim.env.now,
                    "NET",
                    {
                        "event": "RX",
                        "id": self.node_id,
                        "msg": msg.unique_id(),
                        "from": from_nid,
                    },
                )
                if self.router is not None:
                    if msg.is_dtn_bundle():
                        self.router._on_msg_received(deepcopy(msg), from_nid)
                    else:
                        self.router._on_pkt_received(deepcopy(msg), from_nid)
            else:
                # print("Node %d received msg %s from %d (not neighbor)" %
                #      (to_nid, msg, from_nid))
                netsim.net_stats["drop"] += 1
                netsim.nodes[from_nid].router._on_tx_failed(
                    msg.unique_id(), self.node_id
                )
                pons.simulation.event_log(
                    netsim.env.now,
                    "NET",
                    {
                        "event": "RX_FAIL",
                        "id": self.node_id,
                        "msg": msg.unique_id(),
                        "to": from_nid,
                    },
                )


def generate_nodes(
    num_nodes: int,
    offset: int = 0,
    net: List[NetworkSettings] | None = None,
    router: pons.routing.Router | None = None,
):
    nodes = []
    if net == None:
        net = []
    for i in range(num_nodes):
        nodes.append(Node(i + offset, net=deepcopy(net), router=deepcopy(router)))
    return nodes


def generate_nodes_from_graph(
    graph: nx.Graph,
    net: List[NetworkSettings] | None = None,
    router: pons.Router | None = None,
    contactplan: pons.net.plans.CommonContactPlan | None = None,
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
    for i, data in list(graph.nodes().data()):
        if (
            (isinstance(i, str) and i.startswith("net_"))
            or str.upper(graph.nodes[i].get("type", "node")) == "SWITCH"
            or str.upper(graph.nodes[i].get("type", "node")) == "NET"
        ):
            continue
        node_name = data.get("name", "")
        n = Node(i, node_name=node_name, net=deepcopy(net), router=deepcopy(router))
        if data.get("x") is not None:
            n.x = float(data.get("x"))
        if data.get("y") is not None:
            n.y = float(data.get("y"))
        if data.get("z") is not None:
            n.z = float(data.get("z"))
        nodes.append(n)

    return nodes
