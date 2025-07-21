from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional
import logging


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Contact(object):
    timespan: Tuple[float, float]
    nodes: Tuple[int, int]
    bw: int | None = None
    loss: float = 0.0
    delay: float = 0.0
    jitter: float = 0.0
    fixed: bool = False

    def __str__(self) -> str:
        if self.fixed:
            return "Contact(fixed, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)" % (
                self.nodes,
                self.bw,
                self.loss,
                self.delay,
                self.jitter,
            )
        else:
            return (
                "Contact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)"
                % (
                    self.timespan,
                    self.nodes,
                    self.bw,
                    self.loss,
                    self.delay,
                    self.jitter,
                )
            )


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

    def at(self, time: int) -> List[Contact]:
        raise NotImplementedError()

    def next_event(self, time: int) -> Optional[int]:
        raise NotImplementedError()

    def __eq__(self, value: object) -> bool:
        raise NotImplementedError()

    def __hash__(self) -> int:
        raise NotImplementedError()

    def fixed_links(self) -> List[Tuple[int, int]]:
        return []

    def raw_contacts(self) -> List[Contact]:
        """
        Returns a list of all contacts in the contact plan.

        """
        raise NotImplementedError()


class ContactPlan(CommonContactPlan):
    """
    A ContactPlan is a CommonContactPlan that can be used to create contacts.
    It is a factory for Contact objects.
    """

    def __init__(
        self, contacts: List[Contact], loop: bool = False, symmetric: bool = False
    ) -> None:
        self.contacts = contacts
        self.loop = loop
        self.symmetric = symmetric
        self.last_at = -1
        self.last_cache = []
        self.contacts = sorted(self.contacts, key=lambda c: c.timespan[0])
        self.max_time = max((c.timespan[1] for c in self.contacts), default=0.0)

    def get_max_time(self) -> int:
        """Returns the maximum time in the contact plan."""
        return self.max_time

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContactPlan):
            return False
        return (
            self.contacts == other.contacts
            and self.loop == other.loop
            and self.symmetric == other.symmetric
        )

    def raw_contacts(self) -> List[Contact]:
        """
        Returns a list of all contacts in the contact plan.
        """
        return self.contacts

    def __hash__(self) -> int:
        return hash((tuple(self.contacts), self.loop, self.symmetric))

    def all_contacts(self) -> List[Tuple[int, int]]:
        return list(set([(c.nodes[0], c.nodes[1]) for c in self.contacts]))

    def loss_for_contact(self, simtime: float, node1: int, node2: int) -> float:
        current_contacts = self.at(simtime)
        for c in current_contacts:
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                return c.loss
            if (
                c.nodes[0] == node2 and c.nodes[1] == node1 and self.symmetric
            ):  # for symmetric contact plans check the reverse as well
                return c.loss

        return 0.0

    def has_contact(self, simtime: float, node1: int, node2: int) -> bool:
        current_contacts = self.at(simtime)
        for contact in current_contacts:
            if contact.nodes[0] == node1 and contact.nodes[1] == node2:
                return True
            if (
                contact.nodes[0] == node2 and contact.nodes[1] == node1
            ) and self.symmetric:  # Assuming symmetric means the contact is bidirectional

                return True
        return False

    def tx_time_for_contact(
        self, simtime: float, node1: int, node2: int, size: int
    ) -> float:
        current_contacts = self.at(simtime)
        for c in current_contacts:
            if c.bw == 0:  # no bandwidth limit, return a very small time
                return 0.000005 * size
            if c.nodes[0] == node1 and c.nodes[1] == node2:
                # calculate jitter to apply
                jitter = 0
                if c.jitter > 0:
                    jitter = (random.random() - 0.5) * c.jitter
                return size / c.bw + c.delay / 1000 + jitter
            if (
                c.nodes[0] == node2 and c.nodes[1] == node1 and self.symmetric
            ):  # for symmetric contact plans check the reverse as well
                jitter = 0
                if c.jitter > 0:
                    jitter = (random.random() - 0.5) * c.jitter
                return size / c.bw + c.delay / 1000 + jitter
        raise Exception("no contact found")

    def at(self, time: int) -> List[Contact]:
        """Returns all contacts that are active at the given time."""
        if self.last_at == time:
            return self.last_cache
        self.last_at = time
        if self.loop and time > self.max_time:
            time = time % self.get_max_time()
        current_contacts = [
            c for c in self.contacts if c.timespan[0] <= time <= c.timespan[1]
        ]
        self.last_cache = current_contacts
        return current_contacts

    def next_event(self, time: int) -> Optional[int]:
        start_event = float("inf")
        for contact in self.contacts:
            if contact.timespan[0] > time and contact.timespan[0] < start_event:
                start_event = contact.timespan[0]
        end_event = float("inf")
        for contact in self.contacts:
            if contact.timespan[1] > time and contact.timespan[1] < end_event:
                end_event = contact.timespan[1]
        next_time = min(start_event, end_event)
        return int(next_time) if next_time != float("inf") else None

    def fixed_links(self) -> List[Tuple[int, int]]:
        """Returns a list of fixed links in the contact plan."""
        return [(c.nodes[0], c.nodes[1]) for c in self.contacts if c.fixed]

    def get_max_time(self) -> int:
        """Returns the maximum time in the contact plan."""
        return self.max_time


def bandwidth_parser(bw: str) -> int:
    """
    Parses a bandwidth string and returns the bandwidth in bits per second.
    Supports 'mbit', 'kbit', and 'gbit' suffixes.
    """
    if isinstance(bw, str):
        bw = bw.lower()
        if bw.endswith("mbit"):
            return int(bw[:-4]) * 1_000_000
        elif bw.endswith("kbit"):
            return int(bw[:-4]) * 1_000
        elif bw.endswith("gbit"):
            return int(bw[:-4]) * 1_000_000_000
        else:
            return int(bw)
    return bw
