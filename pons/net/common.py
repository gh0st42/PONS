from __future__ import annotations
from pons.event_log import event_log
from pons.net.plans import CommonContactPlan

import random

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pons.routing
    from pons import Node


BROADCAST_ADDR = 0xFFFF


class NetworkSettings(object):
    """A network settings."""

    def __init__(
        self,
        name,
        range,
        bandwidth: int = 54000000,
        loss: float = 0.0,
        delay: float = 0.05,
        contactplan: CommonContactPlan = None,
    ):
        self.name = name
        self.bandwidth = bandwidth
        self.loss = loss
        self.delay = delay
        self.range = range
        self.range_sq = range * range
        self.contactplan = contactplan
        self.env = None

    def __str__(self):
        if self.contactplan is None:
            return "NetworkSettings(%s, %.02f, %.02f, %.02f, %.02f)" % (
                self.name,
                self.range,
                self.bandwidth,
                self.loss,
                self.delay,
            )
        else:
            return "NetworkSettings(%s, %s)" % (self.name, self.contactplan)

    def start(self, netsim):
        self.env = netsim.env

    def tx_time_for_contact(self, simtime: float, node1: int, node2: int, size: int):
        if self.contactplan is None:
            return size / self.bandwidth + self.delay
        else:
            return self.contactplan.tx_time_for_contact(simtime, node1, node2, size)

    def is_lost(self, t: float, src: int, dst: int) -> bool:
        if self.contactplan is None:
            return random.random() < self.loss
        else:
            return random.random() < self.contactplan.loss_for_contact(t, src, dst)

    def has_contact(self, t, src: Node, dst: Node) -> bool:
        if self.contactplan is None:
            dx = src.x - dst.x
            dy = src.y - dst.y
            dz = src.z - dst.z

            # sqrt is expensive, so we use the square of the distance
            # dist = math.sqrt(dx * dx + dy * dy)
            dist = dx * dx + dy * dy + dz * dz
            return dist <= self.range_sq
        else:
            return self.contactplan.has_contact(t, src.node_id, dst.node_id)
