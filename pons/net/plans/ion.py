from __future__ import annotations
from dataclasses import dataclass
from dateutil.parser import parse


from random import random
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional

from pons.net.plans import CommonContactPlan


class IonContactPlan(CommonContactPlan):
    """An ION ContactPlan file."""

    def __init__(self, name: str, contacts=None):
        self.name = name
        if contacts is None:
            self.contacts = []
        self.contacts = contacts

    def __str__(self):
        return "IonContactPlan(%s, %d)" % (self.name, len(self.contacts))

    def fixed_links(self) -> List[Tuple[int, int]]:
        return []

    @classmethod
    def from_file(cls, filename, mapping: Optional[Dict[str, int]] = None):
        if mapping is None:
            mapping = {}
        contacts = []
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip().lower()
                if line.startswith("#") or len(line) < 3 or not line.startswith("a"):
                    # only support adding plan entries
                    continue

                cmd, param1, t_start, t_end, node1, node2, bw_or_range = line.split()
                t_range = (float(t_start), float(t_end))
                if node1 in mapping:
                    node1 = mapping[node1]
                else:
                    node1 = int(node1)
                if node2 in mapping:
                    node2 = mapping[node2]
                else:
                    node2 = int(node2)

                bw_or_range = float(bw_or_range)
                if param1 == "range":
                    # convert range from light seconds to meters
                    bw_or_range = bw_or_range * 299792458
                contacts.append((param1, t_range, node1, node2, bw_or_range))
        return IonContactPlan(filename, contacts)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, IonContactPlan):
            return False
        if self.name != value.name:
            return False
        if len(self.contacts) != len(value.contacts):
            return False
        for i in range(len(self.contacts)):
            if self.contacts[i] != value.contacts[i]:
                return False
        return True

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.contacts)))

    def all_contacts(self) -> List[Tuple[int, int]]:
        all = [(c[2], c[3]) for c in self.contacts]
        # remove duplicates
        return list(set(all))

    def get_entries(self, t):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t]

    def get_contacts(self, t):
        return [
            c
            for c in self.contacts
            if c[1][0] <= t and c[1][1] >= t and c[0] == "contact"
        ]

    def get_ranges(self, t):
        return [
            c
            for c in self.contacts
            if c[1][0] <= t and c[1][1] >= t and c[0] == "range"
        ]

    def get_contacts_for_node(self, t, node_id: int):
        return [
            c
            for c in self.contacts
            if c[1][0] <= t
            and c[1][1] >= t
            and (c[2] == node_id or c[3] == node_id)
            and c[0] == "contact"
        ]

    def get_ranges_for_node(self, t, node_id: int):
        return [
            c
            for c in self.contacts
            if c[1][0] <= t
            and c[1][1] >= t
            and (c[2] == node_id or c[3] == node_id)
            and c[0] == "range"
        ]

    def remove_past_entries(self, t):
        self.contacts = [c for c in self.contacts if c[1][1] >= t]

    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        contacts_of_src = self.get_contacts_for_node(simtime, node1)
        # print("has_contact: %d %d %s " % (node1, node2, contacts_of_src))
        for c in contacts_of_src:
            if c[2] == node2 or c[3] == node2:
                return True
        return False

    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        contacts = self.get_contacts_for_node(simtime, node1)
        for c in contacts:
            if c[2] == node2 or c[3] == node2:
                return 0.0
        raise Exception("no contact found")

    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        contacts = self.get_contacts_for_node(simtime, node1)
        for c in contacts:
            if c[2] == node2 or c[3] == node2:
                ranges = self.get_ranges_for_node(simtime, node1)
                for r in ranges:
                    if r[2] == node2 or r[3] == node2:
                        return size / c[4] + r[4] * 0.00000013
        raise Exception("no contact found")
