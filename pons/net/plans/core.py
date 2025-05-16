from __future__ import annotations
from dataclasses import dataclass
from dateutil.parser import parse


from random import random
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional

from pons.net.plans import Contact, CommonContactPlan


@dataclass(frozen=True)
class CoreContact(Contact):
    timespan: Tuple[int, int]
    nodes: Tuple[int, int]
    bw: int
    loss: float
    delay: float
    jitter: float

    def __str__(self) -> str:
        return (
            "CoreContact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)"
            % (self.timespan, self.nodes, self.bw, self.loss, self.delay, self.jitter)
        )

    @classmethod
    def from_string(
        cls, line: str, mapping: Optional[Dict[str, int]] = None
    ) -> "CoreContact":
        if mapping is None:
            mapping = {}
        line = line.strip()
        if line.startswith("a contact"):
            line = line[9:].strip()
        fields = line.split()
        # print(fields, len(fields))
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
        delay = float(fields[6])
        jitter = float(fields[7])
        return cls(timespan, nodes, bw, loss, delay, jitter)


class CoreContactPlan(CommonContactPlan):
    """A CoreContactPlan file."""

    def __init__(
        self,
        filename: Optional[str] = None,
        contacts: Optional[List[CoreContact]] = None,
        mapping: Optional[Dict[str, int]] = None,
        symmetric: bool = True,
    ) -> None:
        self.loop = False
        self.symmetric = symmetric
        if contacts is None:
            contacts = []
        self.contacts = contacts
        if mapping is None:
            mapping = {}
        if filename:
            self.load(filename, mapping=mapping)
        self.max_time = max([c.timespan[1] for c in self.contacts])
        self.last_at = -1
        self.last_cache = []

    @classmethod
    def from_file(
        cls, filename, mapping: Optional[Dict[str, int]] = None, symmetric: bool = True
    ) -> CoreContactPlan:
        if mapping is None:
            mapping = {}
        plan = cls(filename, mapping=mapping, symmetric=symmetric)
        return plan

    @classmethod
    def from_csv_file(
        cls,
        filename,
        mapping: Optional[Dict[str, int]] = None,
        parse_header: bool = False,
        delimiter: str = ",",
        node_rename_mapping: Optional[Dict[str, str]] = None,
        speedup=1,
        symmetric: bool = True,
    ) -> CoreContactPlan:
        if mapping is None:
            mapping = {}
        if node_rename_mapping is None:
            node_rename_mapping = {}
        contacts = []
        sim_start = 0
        with open(filename, "r") as f:
            if parse_header:
                hdr = f.readline()
                if "# Simulation starting time:" in hdr:
                    sim_start = parse(hdr.split(":")[1].strip(), ignoretz=True)

            for line in f.readlines():
                line = line.strip()
                fields = line.split(delimiter)
                if len(fields) != 5:
                    raise ValueError(
                        "Invalid CSV contact line (expected: node1,node2,start,end,duration): %s"
                        % line
                    )

                # strip all fields
                fields = [f.strip() for f in fields]

                start = parse(fields[2], ignoretz=True)
                end = parse(fields[3], ignoretz=True)

                node1 = fields[0]
                node2 = fields[1]

                if node1 in node_rename_mapping:
                    node1 = node_rename_mapping[node1]
                if node2 in node_rename_mapping:
                    node2 = node_rename_mapping[node2]

                if node1 in mapping:
                    node1 = mapping[node1]
                else:
                    node1 = int(node1)
                if node2 in mapping:
                    node2 = mapping[node2]
                else:
                    node2 = int(node2)

                contact = (start, end, node1, node2, int(fields[4]))
                contacts.append(contact)
        contacts.sort(key=lambda x: x[0])
        if sim_start == 0:
            sim_start = contacts[0][0]

        # adjust start times relative in seconds to sim_start
        contacts = [
            (
                int((start - sim_start).total_seconds()),
                int((end - sim_start).total_seconds()),
                src,
                dst,
                duration,
            )
            for start, end, src, dst, duration in contacts
        ]
        # apply speedup
        contacts = [
            (int(start / speedup), int(end / speedup), src, dst, duration)
            for start, end, src, dst, duration in contacts
        ]
        contacts = [
            CoreContact((start, end), (src, dst), 0, 0, 0, 0)
            for start, end, src, dst, duration in contacts
        ]
        plan = cls(contacts=contacts, mapping=mapping, symmetric=symmetric)
        return plan

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, CoreContactPlan):
            return False
        if self.loop != value.loop:
            return False
        if len(self.contacts) != len(value.contacts):
            return False
        for i in range(len(self.contacts)):
            if self.contacts[i] != value.contacts[i]:
                return False
        return True

    def __hash__(self) -> int:
        return hash((self.loop, tuple(self.contacts)))

    def __str__(self) -> str:
        return "CoreContactPlan(loop=%r, #contacts=%d)" % (
            self.loop,
            len(self.contacts),
        )

    def load(self, filename: str, mapping: Optional[Dict[str, int]] = None) -> None:
        if mapping is None:
            mapping = {}
        contacts = []
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or line.startswith("//") or len(line) < 6:
                    continue
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
                        # print(contact)
                        contacts.append(contact)
        self.contacts = contacts

    def all_contacts(self) -> List[Tuple[int, int]]:
        all = [(c.nodes[0], c.nodes[1]) for c in self.contacts]
        # remove duplicates
        return list(set(all))

    def clean(self, time: int) -> None:
        self.contacts = [c for c in self.contacts if c.timespan[1] >= time]

    def at(self, time: int) -> List[CoreContact]:
        """Returns the list of contacts at the given time."""
        # orig = time
        # if self.loop:
        #     time = time % (math.floor(self.get_max_time() + 0.5))
        if time == self.last_at:
            # print("cache hit", time, self.last_at)
            return self.last_cache

        # print("cache miss", time, self.last_at)
        self.last_at = time

        if self.loop:
            time = time % self.get_max_time()

        contacts = [
            c for c in self.contacts if time >= c.timespan[0] and time <= c.timespan[1]
        ]
        self.last_cache = contacts

        if not self.loop:
            # only clean old entries if not in loop mode

            # print("at: %d (%d) %s" % (time, orig, [str(c) for c in contacts]))
            tenth_time = self.get_max_time() / 10
            # check if time is a multiple of 10% of the max time
            if time % tenth_time == 0:
                self.clean(time)

        return contacts

    def next_event(self, time: int) -> Optional[int]:
        orig = time
        if self.loop:
            time = time % self.get_max_time()

        nexts_1 = [c.timespan[0] for c in self.contacts if c.timespan[0] > time]
        nexts_2 = [c.timespan[1] for c in self.contacts if c.timespan[1] > time]
        nexts = nexts_1 + nexts_2
        if len(nexts) == 0:
            return None
        if not self.loop:
            return min(nexts)
        else:
            return min(nexts) + (orig - time)

    # def next_deactivation(self, time : int) -> Optional[int]:
    #   """Returns the next deactivation time.
    #   """
    #   deactivations = [c.timespan[1] for c, s in self.contacts.items() if s == ContactState.LIVE and c.timespan[1] >= time]
    #   if len(deactivations) == 0:
    #     return None
    #   return min(deactivations)

    def get_max_time(self) -> int:
        """Returns the maximum time in the contact plan."""
        return self.max_time

    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        current_contacts = self.at(simtime)
        # print("[ %f ] has_contact: %d %d | %s" % (simtime, node1, node2, current_contacts[0]))
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return True
            if (
                c.nodes[0] == node2 and c.nodes[1] == node1 and self.symmetric
            ):  # for symmetric contact plans check the reverse as well
                return True
        return False

    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        current_contacts = self.at(simtime)
        # print("[ %f ] loss_for_contact: %d %d | %s" % (simtime, node1, node2, current_contacts))
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return c.loss
            if (
                c.nodes[0] == node2 and c.nodes[1] == node1 and self.symmetric
            ):  # for symmetric contact plans check the reverse as well
                return c.loss

        return 0.0

    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        current_contacts = self.at(simtime)
        for c in current_contacts:
            if c.bw == 0:
                return 0.000005 * size
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                # calculate jitter to apply
                jitter = 0
                if c.jitter > 0:
                    jitter = (random() - 0.5) * c.jitter
                return size / c.bw + c.delay / 1000 + jitter
            if (
                c.nodes[0] == node2 and c.nodes[1] == node1 and self.symmetric
            ):  # for symmetric contact plans check the reverse as well
                jitter = 0
                if c.jitter > 0:
                    jitter = (random() - 0.5) * c.jitter
                return size / c.bw + c.delay / 1000 + jitter
        raise Exception("no contact found")

    def fixed_links(self) -> List[Tuple[int, int]]:
        return []
