from __future__ import annotations
from copy import deepcopy

import networkx as nx

from typing import TYPE_CHECKING, List, Tuple, Optional

from .contactplan import CommonContactPlan


class NetworkPlan(CommonContactPlan):
    def __init__(
        self, G: nx.Graph, contacts: Optional[CommonContactPlan] = None
    ) -> None:
        self.G = G
        self.set_contacts(contacts)
        self.mapping = {}

    # set the contact plan and remove all edges that are in the contact plan from the static graph
    def set_contacts(self, contacts: CommonContactPlan) -> None:
        self.contacts = contacts
        if contacts is not None:
            for c in self.contacts.all_contacts():
                self.G.remove_edge(c[0], c[1])

    def __str__(self) -> str:
        return "NetworkPlan(%s)" % (self.G)

    # return the loss for a contact between two nodes
    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        if self.G.has_edge(node1, node2):
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
                return 0.000005 * size
            else:
                return self.contacts.tx_time_for_contact(simtime, node1, node2, size)

    def nodes(self) -> List[int]:
        return list(self.G.nodes())

    def connections(self) -> List[Tuple[int, int]]:
        return list(self.G.edges())

    @classmethod
    def from_graphml(cls, filename) -> NetworkPlan:
        G = nx.read_graphml(filename)
        # if there are nodes starting with net_ remove them and directly add edges between their adjacent nodes
        from copy import deepcopy

        for n in deepcopy(G.nodes()):
            if n.startswith("net_"):
                neighbors = list(G.neighbors(n))
                for i in range(len(neighbors)):
                    for j in range(i + 1, len(neighbors)):
                        G.add_edge(neighbors[i], neighbors[j])
                G.remove_node(n)
        print("removed hub nodes")
        print(G.nodes())
        print(G.edges())

        # rename all node names to integers corresponding to their index
        mapping = {n: i for i, n in enumerate(G.nodes())}
        print(mapping)
        G = nx.relabel_nodes(G, mapping)
        plan = cls(G)
        plan.mapping = mapping
        return plan
