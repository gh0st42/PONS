from typing import TYPE_CHECKING, Dict, List, Tuple, Optional


class Contact(object):
    timespan: Tuple[int, int]
    nodes: Tuple[int, int]
    bw: int
    loss: float
    delay: float
    jitter: float

    def __str__(self) -> str:
        return "Contact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)" % (
            self.timespan,
            self.nodes,
            self.bw,
            self.loss,
            self.delay,
            self.jitter,
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
