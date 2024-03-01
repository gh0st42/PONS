from __future__ import annotations

import networkx as nx

from typing import TYPE_CHECKING, List, Tuple, Optional

from .contactplan import CommonContactPlan

class NetworkPlan(CommonContactPlan):
    def __init__(self, G : nx.Graph) -> None:
        self.G = G

    def __str__(self) -> str:
        return "NetworkPlan(%s)" % (self.G)

    def loss_for_contact(self, simtime: float, node1 : int, node2 : int) -> float:
        return 0.0

    def has_contact(self, simtime: float, node1 : int, node2 : int) -> bool:
        return self.G.has_edge(node1, node2)

    def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int) -> float:
        return 1.0

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
                    for j in range(i+1, len(neighbors)):
                        G.add_edge(neighbors[i], neighbors[j])
                G.remove_node(n)
        print("removed hub nodes")
        print(G.nodes())
        print(G.edges())

        # rename all node names to integers corresponding to their index
        mapping = {n: i for i,n in enumerate(G.nodes())}
        print(mapping)
        G = nx.relabel_nodes(G, mapping)
        plan = cls(G)
        return plan