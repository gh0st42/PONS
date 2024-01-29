from __future__ import annotations

import random
import math

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pons.routing
    from pons import Node


BROADCAST_ADDR = 0xFFFF

class ContactPlan(object):
    """A ContactPlan file.
    """

    def __init__(self, name : str, contacts=[]):
        self.name = name
        self.contacts = contacts

    def __str__(self):
        return "ContactPlan(%s, %d)" % (self.name, len(self.contacts))

    @classmethod
    def from_file(cls, filename):
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
                node1 = int(node1)
                node2 = int(node2)
                bw_or_range = float(bw_or_range)
                if param1 == "range":
                    # convert range from light seconds to meters
                    bw_or_range = bw_or_range * 299792458
                contacts.append((param1, t_range, node1, node2, bw_or_range))
        return ContactPlan(filename, contacts)
    
    def get_entries(self, t):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t]
    
    def get_contacts(self, t):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and c[0] == "contact"]
    
    def get_ranges(self, t):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and c[0] == "range"]
    
    def get_contacts_for_node(self, t, node_id):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and (c[2] == node_id or c[3] == node_id) and c[0] == "contact"]
    
    def get_ranges_for_node(self, t, node_id):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and (c[2] == node_id or c[3] == node_id) and c[0] == "range"]
    
    def remove_past_entries(self, t):
        self.contacts = [c for c in self.contacts if c[1][1] >= t]
                


class NetworkSettings(object):
    """A network settings.
    """

    def __init__(self, name, range, bandwidth : int = 54000000, loss : float =0.0, delay : float = 0.05, contactplan : ContactPlan = None):
        self.name = name
        self.bandwidth = bandwidth
        self.loss = loss
        self.delay = delay
        self.range = range
        self.range_sq = range * range
        self.contactplan = contactplan

    def __str__(self):
        if self.contactplan is None:
            return "NetworkSettings(%s, %.02f, %.02f, %.02f, %.02f)" % (self.name, self.range, self.bandwidth, self.loss, self.delay)
        else:
            return "NetworkSettings(%s, %s)" % (self.name, self.contactplan)

    def tx_time(self, size):
        return size / self.bandwidth + self.delay
    
    def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int):
        if self.contactplan is None:
            return size / self.bandwidth + self.delay
        else:
            contacts = self.contactplan.get_contacts_for_node(simtime, node1)
            for c in contacts:
                if c[2] == node2 or c[3] == node2:
                    ranges = self.contactplan.get_ranges_for_node(simtime, node1)
                    for r in ranges:
                        if r[2] == node2 or r[3] == node2:
                            return size /c[4] + r[4]*0.00000013
            raise Exception("no contact found")

    def is_lost(self):
        return random.random() < self.loss
    
    def has_contact(self, t, src: Node, dst: Node):
        if self.contactplan is None:
            return False
        else:
            contacts_of_src = self.contactplan.get_contacts_for_node(t, src.id)
            print("has_contact: %d %d %s " % (src.id, dst.id, contacts_of_src))
            for c in contacts_of_src:
                if c[2] == dst.id or c[3] == dst.id:
                    return True
            return False

    def is_in_range(self, src: Node, dst: Node):
        if self.contactplan is not None:
            return False
        dx = src.x - dst.x
        dy = src.y - dst.y
        dz = src.z - dst.z

        # sqrt is expensive, so we use the square of the distance
        # dist = math.sqrt(dx * dx + dy * dy)
        dist = dx * dx + dy * dy + dz * dz
        return dist <= self.range_sq
    