from __future__ import annotations
from copy import deepcopy

import networkx as nx
import sys
from random import random

from typing import TYPE_CHECKING, List, Tuple, Optional

from .plans import CommonContactPlan
import pons


class NetworkPlan(CommonContactPlan):
    def __init__(
        self, G: nx.Graph, contacts: Optional[CommonContactPlan] = None
    ) -> None:
        self.G = G
        self.full_graph = deepcopy(G)
        self.set_contacts(contacts)
        self.mapping = {}

    def active_links_at(self, time: int) -> List[Tuple[int, int]]:
        contacts = []
        if self.contacts is not None:
            for c in self.contacts.at(time):
                contacts.append(c.nodes)
        for e in self.G.edges():
            contacts.append(e)
        return contacts

    def fixed_links(self) -> List[Tuple[int, int]]:
        return self.G.edges()

    def next_event(self, time: int) -> int | None:
        if self.contacts is not None:
            return self.contacts.next_event(time)
        return None

    def __eq__(self, value: object) -> bool:
        if self.G != value.G:
            return False
        if self.contacts != value.contacts:
            return False
        return True

    def __hash__(self) -> int:
        contacts_hash = 0
        if self.contacts is not None:
            contacts_hash = hash(tuple(self.contacts.all_contacts()))
        return contacts_hash

    # set the contact plan and remove all edges that are in the contact plan from the static graph
    def set_contacts(self, contacts: CommonContactPlan) -> None:
        self.contacts = contacts
        if contacts is not None:
            for c in self.contacts.all_contacts():
                self.full_graph.add_edge(c[0], c[1])
                try:
                    self.G.remove_edge(c[0], c[1])
                except nx.NetworkXError:
                    print("WARNING: Edge %s not in graph" % str(c), file=sys.stderr)

    def __str__(self) -> str:
        return "NetworkPlan(%s)" % (self.G)

    # return the loss for a contact between two nodes
    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        if self.G.has_edge(node1, node2):
            link_props = self.G.get_edge_data(node1, node2, default={"loss": 0.0})
            if "loss" in link_props:
                return link_props["loss"]
            else:
                return 0.0
        if self.contacts is not None:
            return self.contacts.loss_for_contact(simtime, node1, node2)
        else:
            return 100.0

    # return whether there is a contact between two nodes
    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        if self.contacts is None:
            return self.G.has_edge(node1, node2)
        else:
            return self.contacts.has_contact(simtime, node1, node2) or self.G.has_edge(
                node1, node2
            )

    # return the transmission time for a contact between two nodes for a given size
    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        if self.contacts is None:
            return 0.000005 * size
        else:
            if self.G.has_edge(node1, node2):
                link_props = self.G.get_edge_data(
                    node1,
                    node2,
                    default={"loss": 0.0, "delay": 0.0, "jitter": 0.0, "bw": 0},
                )
                jitter = link_props.get("jitter", 0)
                if jitter > 0:
                    jitter = jitter * (random() - 0.5)

                tx_time = link_props.get("delay", 0) / 1000 + jitter
                bw = link_props.get("bw", 0)
                if bw > 0:
                    tx_time += size / bw
                if tx_time == 0:
                    # 0 delay is not allowed for scheduling in the simulator
                    tx_time = 0.000005 * size
                return tx_time
            else:
                return self.contacts.tx_time_for_contact(simtime, node1, node2, size)

    def nodes(self) -> List[int]:
        return list(self.G.nodes())

    def connections(self) -> List[Tuple[int, int]]:
        return list(self.G.edges())

    def connections_at_time(self, time: float) -> List[Tuple[int, int]]:
        static_links = list(self.G.edges())
        if self.contacts is None:
            return static_links
        else:
            dyn_links = self.contacts.at(time)
            # convert to list of tuples with node ids
            dyn_links = [l.nodes for l in dyn_links]
            return static_links + dyn_links

    def generate_nodes(self, router=None) -> None:
        nodes = []
        net = pons.NetworkSettings("contactplan", range=0, contactplan=self)
        for node_id, data in list(self.G.nodes(data=True)):
            router2 = deepcopy(router)
            router2.my_id = node_id
            node = pons.Node(node_id, data["name"], net=[deepcopy(net)], router=router2)
            node.x = data.get("x", 0)
            node.y = data.get("y", 0)
            node.z = data.get("z", 0)
            nodes.append(node)
        return nodes

    @classmethod
    def from_graphml(cls, filename: str) -> NetworkPlan:
        G = nx.read_graphml(filename)
        # if there are nodes starting with net_ remove them and directly add edges between their adjacent nodes
        from copy import deepcopy

        for n in deepcopy(G.nodes()):
            if (
                (isinstance(n, str) and n.startswith("net_"))
                or str.upper(G.nodes[n].get("type", "node")) == "SWITCH"
                or str.upper(G.nodes[n].get("type", "node")) == "NET"
            ):
                neighbors = list(G.neighbors(n))
                for i in range(len(neighbors)):
                    for j in range(i + 1, len(neighbors)):
                        G.add_edge(neighbors[i], neighbors[j])
                G.remove_node(n)

        # check if all node names are integers
        if all([isinstance(n, int) or n.isnumeric() for n in G.nodes()]):
            print("Nodes are already integers")
            mapping = {n: int(n) for n in G.nodes()}
            for n in G.nodes:
                name = G.nodes[n].get("name", None)
                if name is not None:
                    print("Mapping node %s to %d" % (name, int(n)))
                    mapping[name] = int(n)
        else:
            print("Renaming nodes")
            # rename all node names to integers corresponding to their index
            mapping = {n: i for i, n in enumerate(G.nodes())}
            print(mapping)
        G = nx.relabel_nodes(G, mapping)

        # remove edges that have data of "dynamic_link" set to True
        for e in deepcopy(G.edges()):
            if G.get_edge_data(*e).get("dynamic_link", False):
                print("Removing dynamic link edge %s" % str(e), file=sys.stderr)
                G.remove_edge(*e)

        plan = cls(G)
        plan.mapping = mapping
        return plan
