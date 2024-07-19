from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple, Optional


class CommonContactPlan(object):
    def all_contacts(self) -> List[Tuple[int, int]]:
        raise NotImplementedError()

    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        raise NotImplementedError()

    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        raise NotImplementedError()

    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        raise NotImplementedError()

    def at(self, time: int) -> List[CoreContact]:
        raise NotImplementedError()


class CoreContact(object):
    def __init__(
        self,
        timespan: Tuple[int, int],
        nodes: Tuple[int, int],
        bw: int,
        loss: float,
        delay: float,
        jitter: float,
    ) -> None:
        self.timespan = timespan
        self.nodes = nodes
        self.bw = bw
        self.loss = loss
        self.delay = delay
        self.jitter = jitter

    def __str__(self) -> str:
        return (
            "CoreContact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)"
            % (self.timespan, self.nodes, self.bw, self.loss, self.delay, self.jitter)
        )

    @classmethod
    def from_string(cls, line: str, mapping: Dict[str, int] = {}) -> "CoreContact":
        line = line.strip()
        if line.startswith("a contact"):
            line = line[9:].strip()
        fields = line.split()
        print(fields, len(fields))
        if len(fields) != 8:
            raise ValueError("Invalid CoreContact line: %s" % line)
        timespan = (int(fields[0]), int(fields[1]))

        if fields[2] in mapping:
            fields[2] = mapping[fields[2]]
        else:
            fields[2] = int(fields[2])
        if fields[3] in mapping:
            fields[3] = mapping[fields[3]]
        else:
            fields[3] = int(fields[3])

        nodes = (fields[2], fields[3])
        bw = int(
            fields[4]
            .replace("mbit", "000000")
            .replace("kbit", "000")
            .replace("gbit", "000000000")
        )
        loss = float(fields[5])
        delay = int(fields[6])
        jitter = int(fields[7])
        return cls(timespan, nodes, bw, loss, delay, jitter)


class CoreContactPlan(object):
    """A CoreContactPlan file."""

    def __init__(
        self,
        filename: str = None,
        contacts: List[CoreContact] = {},
        mapping: Dict[str, int] = {},
    ) -> None:
        self.loop = False
        self.contacts = contacts
        if filename:
            self.load(filename, mapping=mapping)

    @classmethod
    def from_file(cls, filename, mapping: Dict[str, int] = {}) -> CoreContactPlan:
        plan = cls(filename, mapping=mapping)
        return plan

    def __str__(self) -> str:
        return "CoreContactPlan(loop=%r, #contacts=%d)" % (
            self.loop,
            len(self.contacts),
        )

    def load(self, filename: str, mapping: Dict[str, int] = {}) -> None:
        contacts = []
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                fields = line.split()
                if len(fields) == 3 and fields[0] == "s":
                    if fields[1] == "loop":
                        if fields[2] == "1":
                            self.loop = True
                        else:
                            self.loop = False
                elif len(fields) > 4 and fields[0] == "a":
                    if fields[1] == "contact":
                        contact = CoreContact.from_string(line, mapping=mapping)
                        print(contact)
                        contacts.append(contact)
        self.contacts = contacts

    def all_contacts(self) -> List[Tuple[int, int]]:
        all = [(c.nodes[0], c.nodes[1]) for c in self.contacts]
        # remove duplicates
        return list(set(all))

    def at(self, time: int) -> List[CoreContact]:
        """Returns the list of contacts at the given time."""
        orig = time
        if self.loop:
            time = time % self.get_max_time()
        contacts = [
            c for c in self.contacts if c.timespan[0] <= time and c.timespan[1] >= time
        ]
        # print("at: %d (%d) %s" % (time, orig, [str(c) for c in contacts]))
        return contacts

    # def next_deactivation(self, time : int) -> Optional[int]:
    #   """Returns the next deactivation time.
    #   """
    #   deactivations = [c.timespan[1] for c, s in self.contacts.items() if s == ContactState.LIVE and c.timespan[1] >= time]
    #   if len(deactivations) == 0:
    #     return None
    #   return min(deactivations)

    def get_max_time(self) -> int:
        """Returns the maximum time in the contact plan."""
        return max([c.timespan[1] for c in self.contacts])

    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        current_contacts = self.at(simtime)
        # print("[ %f ] has_contact: %d %d | %s" % (simtime, node1, node2, current_contacts[0]))
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return True
            if c.nodes[0] == node2 and c.nodes[1] == node1:
                return True
        return False

    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        current_contacts = self.at(simtime)
        # print("[ %f ] loss_for_contact: %d %d | %s" % (simtime, node1, node2, current_contacts))
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return c.loss
            if c.nodes[0] == node2 and c.nodes[1] == node1:
                return c.loss
        return 0.0

    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        current_contacts = self.at(simtime)
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return size / c.bw + c.delay
            if c.nodes[0] == node2 and c.nodes[1] == node1:
                return size / c.bw + c.delay
        raise Exception("no contact found")


class ContactPlan(CommonContactPlan):
    """A ContactPlan file."""

    def __init__(self, name: str, contacts=[]):
        self.name = name
        self.contacts = contacts

    def __str__(self):
        return "ContactPlan(%s, %d)" % (self.name, len(self.contacts))

    @classmethod
    def from_file(cls, filename, mapping: Dict[str, int] = {}):
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
        return ContactPlan(filename, contacts)

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
