from __future__ import annotations
from copy import deepcopy

import networkx as nx
import sys
from random import random
import logging

logger = logging.getLogger(__name__)

from typing import TYPE_CHECKING, List, Tuple, Optional

from .plans import CommonContactPlan
import pons


class NetworkPlan(CommonContactPlan):
    def __init__(
        self, G: nx.Graph, contacts: Optional[CommonContactPlan] = None
    ) -> None:
        self.G = deepcopy(G)
        self.full_graph = deepcopy(G)
        self.set_contacts(contacts)
        self.mapping = {}

    def active_links_at(self, time: int) -> List[Tuple[int, int]]:
        contacts = []
        if self.contactplan is not None:
            for c in self.contactplan.at(time):
                contacts.append(c.nodes)
        for e in self.G.edges():
            contacts.append(e)
        return contacts

    def fixed_links(self) -> List[Tuple[int, int]]:
        return self.G.edges()

    def next_event(self, time: int) -> int | None:
        if self.contactplan is not None:
            return self.contactplan.next_event(time)
        return None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, NetworkPlan):
            logger.debug("Comparing NetworkPlan with non-NetworkPlan object")
            return False

        if set(self.fixed_links()) != set(value.fixed_links()):
            logger.debug("Fixed links are not equal")
            return False
        if self.all_contacts() != value.all_contacts():
            logger.debug("All contacts are not equal")
            return False
        if self.raw_contacts() != value.raw_contacts():
            logger.debug("Raw contacts are not equal")
            return False

        return True

    def __hash__(self) -> int:
        contacts_hash = 0
        if self.contactplan is not None:
            contacts_hash = hash(tuple(self.contactplan.all_contacts()))
        return contacts_hash

    def raw_contacts(self) -> List[pons.Contact]:
        if self.contactplan is not None:
            return self.contactplan.raw_contacts()
        else:
            return []

    def all_contacts(self) -> List[Tuple[int, int]]:
        if self.contactplan is not None:
            from_cp = self.contactplan.all_contacts()
            fixed = list(self.fixed_links())
            merged_unique = set(from_cp + fixed)
            return list(merged_unique)
        else:
            return list(self.G.edges())

    # set the contact plan and remove all edges that are in the contact plan from the static graph
    def set_contacts(self, contacts: CommonContactPlan) -> None:
        self.contactplan = contacts
        if contacts is not None:
            # merge fixed links with contacts
            for fixed in contacts.fixed_links():
                if not fixed in self.G.edges():
                    self.G.add_edge(*fixed)
                    self.full_graph.add_edge(*fixed)
            # fixed = self.fixed_links()

            # remove edges that are in the contact plan from the static graph
            for c in self.contactplan.raw_contacts():
                if c.fixed:
                    print("Skipping fixed contact %s" % str(c))
                    continue
                c = c.nodes
                # print("Removing contact %s from static graph" % str(c))
                # print(
                #     self.G.edges(data=True),
                #     c in self.G.edges(),
                #     tuple(c) in self.G.edges(),
                # )

                self.full_graph.add_edge(c[0], c[1])
                try:
                    # if c not in fixed:
                    self.G.remove_edge(c[0], c[1])
                    # print("Removed: ", self.G.edges)

                except nx.NetworkXError:
                    logger.debug("Edge %s was not in graph" % str(c))

    def __str__(self) -> str:
        return "NetworkPlan(%s)" % (self.G)

    def at(self, time: int) -> List[pons.Contact]:
        contacts = []
        if self.contactplan is not None:
            contacts = self.contactplan.at(time)
        for e in self.G.edges():
            link_props = self.G.get_edge_data(*e, default={})
            # if no contact plan is set, we do not have a max duration, so we set it to sys.maxsize * 2 + 1
            contact = pons.Contact(
                timespan=(0, sys.maxsize * 2 + 1),
                nodes=e,
                bw=link_props.get("bw", 0),
                loss=link_props.get("loss", 0.0),
                delay=link_props.get("delay", 0.0),
                jitter=link_props.get("jitter", 0.0),
                fixed=True,
            )
            contacts.append(contact)
        return contacts

    # return the loss for a contact between two nodes
    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        if self.G.has_edge(node1, node2):
            link_props = self.G.get_edge_data(node1, node2, default={"loss": 0.0})
            if "loss" in link_props:
                return link_props["loss"]
            else:
                return 0.0
        if self.contactplan is not None:
            return self.contactplan.loss_for_contact(simtime, node1, node2)
        else:
            return 100.0

    # return whether there is a contact between two nodes
    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        if self.contactplan is None:
            return self.G.has_edge(node1, node2)
        else:
            return self.contactplan.has_contact(
                simtime, node1, node2
            ) or self.G.has_edge(node1, node2)

    # return the transmission time for a contact between two nodes for a given size
    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        if self.contactplan is None:
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
                return self.contactplan.tx_time_for_contact(simtime, node1, node2, size)

    def nodes(self) -> List[int]:
        return list(self.G.nodes())

    def connections(self) -> List[Tuple[int, int]]:
        return list(self.G.edges())

    def connections_at_time(self, time: float) -> List[Tuple[int, int]]:
        static_links = list(self.fixed_links())
        if self.contactplan is None:
            return static_links
        else:
            dyn_links = self.contactplan.at(time)
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
            logger.debug("Nodes are already integers")
            mapping = {n: int(n) for n in G.nodes()}
            for n in G.nodes:
                name = G.nodes[n].get("name", None)
                if name is not None:
                    logger.debug("Mapping node %s to %d" % (name, int(n)))
                    mapping[name] = int(n)
        else:
            logger.debug("Renaming nodes")
            # rename all node names to integers corresponding to their index
            mapping = {n: i for i, n in enumerate(G.nodes())}
            logger.debug("Node mapping: %s", mapping)
        G = nx.relabel_nodes(G, mapping)

        # remove edges that have data of "dynamic_link" set to True
        for e in deepcopy(G.edges()):
            if G.get_edge_data(*e).get("dynamic_link", False):
                logger.debug("Removing dynamic link edge %s" % str(e))
                G.remove_edge(*e)

        plan = cls(G)
        plan.mapping = mapping
        return plan
