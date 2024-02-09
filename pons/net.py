from __future__ import annotations

import random
import math

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    import pons.routing
    from pons import Node


BROADCAST_ADDR = 0xFFFF

class CommonContactPlan(object):
  def loss_for_contact(self, simtime: float, node1 : int, node2 : int) -> float:
      raise NotImplementedError()
  
  def has_contact(self, simtime: float, node1 : int, node2 : int) -> bool:
    raise NotImplementedError()
  
  def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int) -> float:
    raise NotImplementedError()


class CoreContact(object):
  def __init__(self, timespan : Tuple[int, int], nodes : Tuple[int, int], bw : int, loss : float, delay : float, jitter : float) -> None:
      self.timespan = timespan
      self.nodes = nodes
      self.bw = bw
      self.loss = loss
      self.delay = delay
      self.jitter = jitter

  def __str__(self) -> str:
    return "CoreContact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)" % (self.timespan, self.nodes, self.bw, self.loss, self.delay, self.jitter)
  
  @classmethod
  def from_string(cls, line : str) -> 'CoreContact':
    line = line.strip()
    if line.startswith('a contact'):
      line = line[9:].strip()
    fields = line.split()
    print(fields, len(fields))
    if len(fields) != 8:
      raise ValueError("Invalid CoreContact line: %s" % line)
    timespan = (int(fields[0]), int(fields[1]))
    nodes = (int(fields[2]), int(fields[3]))
    bw = int(fields[4])
    loss = float(fields[5])
    delay = int(fields[6])
    jitter = int(fields[7])
    return cls(timespan, nodes, bw, loss, delay, jitter)

class CoreContactPlan(object):
    """A CoreContactPlan file.
    """

    def __init__(self, filename : str = None, contacts : List[CoreContact] = {}) -> None:
        self.loop = False
        self.contacts = contacts
        if filename:
            self.load(filename)
    
    @classmethod
    def from_file(cls, filename) -> CoreContactPlan:
        plan = cls(filename)
        return plan

    def __str__(self) -> str:
      return "CoreContactPlan(loop=%r, #contacts=%d)" % (self.loop, len(self.contacts))
       
    def load(self, filename : str) -> None:
        contacts = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                fields = line.split()
                if len(fields) == 3 and fields[0] == 's':
                  if fields[1] == 'loop':
                      if fields[2] == '1':
                        self.loop = True
                      else:
                        self.loop = False
                elif len(fields) > 4 and fields[0] == 'a':
                  if fields[1] == 'contact':
                    contact = CoreContact.from_string(line)
                    print(contact)
                    contacts.append(contact)
        self.contacts = contacts
    
    def at(self, time : int) -> List[CoreContact]:
      """Returns the list of contacts at the given time.
      """
      orig = time
      if self.loop:
        time = time % self.get_max_time()
      contacts = [c for c in self.contacts if c.timespan[0] <= time and c.timespan[1] >= time]
      #print("at: %d (%d) %s" % (time, orig, [str(c) for c in contacts]))
      return contacts
    
    # def next_deactivation(self, time : int) -> Optional[int]:
    #   """Returns the next deactivation time.
    #   """
    #   deactivations = [c.timespan[1] for c, s in self.contacts.items() if s == ContactState.LIVE and c.timespan[1] >= time]
    #   if len(deactivations) == 0:
    #     return None
    #   return min(deactivations)
    
    
    def get_max_time(self) -> int:
      """Returns the maximum time in the contact plan.
      """
      return max([c.timespan[1] for c in self.contacts])
    
    def has_contact(self, simtime: float, node1 : int, node2 : int) -> bool:
      current_contacts = self.at(simtime)
      # print("[ %f ] has_contact: %d %d | %s" % (simtime, node1, node2, current_contacts[0]))
      for c in current_contacts:
          if c.nodes[0] == node1 and c.nodes[1] == node2:
              return True
          if c.nodes[0] == node2 and c.nodes[1] == node1:
              return True
      return False
  
    def loss_for_contact(self, simtime: float, node1 : int, node2 : int) -> float:
      current_contacts = self.at(simtime)
      #print("[ %f ] loss_for_contact: %d %d | %s" % (simtime, node1, node2, current_contacts))
      for c in current_contacts:
          if c.nodes[0] == node1 and c.nodes[1] == node2:
              return c.loss
          if c.nodes[0] == node2 and c.nodes[1] == node1:
              return c.loss
      return 0.0
    
    def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int) -> float:
      current_contacts = self.at(simtime)
      for c in current_contacts:
          if c.nodes[0] == node1 and c.nodes[1] == node2:
              return size / c.bw + c.delay
          if c.nodes[0] == node2 and c.nodes[1] == node1:
              return size / c.bw + c.delay
      raise Exception("no contact found")

class ContactPlan(CommonContactPlan):
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
    
    def get_contacts_for_node(self, t, node_id : int):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and (c[2] == node_id or c[3] == node_id) and c[0] == "contact"]
    
    def get_ranges_for_node(self, t, node_id : int):
        return [c for c in self.contacts if c[1][0] <= t and c[1][1] >= t and (c[2] == node_id or c[3] == node_id) and c[0] == "range"]
    
    def remove_past_entries(self, t):
        self.contacts = [c for c in self.contacts if c[1][1] >= t]
    
    def has_contact(self, simtime: float, node1 : int, node2 : int) -> bool:
      contacts_of_src = self.get_contacts_for_node(simtime, node1)
      #print("has_contact: %d %d %s " % (node1, node2, contacts_of_src))
      for c in contacts_of_src:
          if c[2] == node2 or c[3] == node2:
              return True
      return False
  
    def loss_for_contact(self, simtime: float, node1 : int, node2 : int) -> float:
      contacts = self.get_contacts_for_node(simtime, node1)
      for c in contacts:
          if c[2] == node2 or c[3] == node2:
              return 0.0
      raise Exception("no contact found")
    
    def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int) -> float:
      contacts = self.get_contacts_for_node(simtime, node1)
      for c in contacts:
          if c[2] == node2 or c[3] == node2:
              ranges = self.get_ranges_for_node(simtime, node1)
              for r in ranges:
                  if r[2] == node2 or r[3] == node2:
                      return size /c[4] + r[4]*0.00000013
      raise Exception("no contact found")
                


class NetworkSettings(object):
    """A network settings.
    """

    def __init__(self, name, range, bandwidth : int = 54000000, loss : float =0.0, delay : float = 0.05, contactplan : CommonContactPlan = None):
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
    
    def tx_time_for_contact(self, simtime : float, node1 : int, node2 : int, size : int):
        if self.contactplan is None:
            return size / self.bandwidth + self.delay
        else:
            return self.contactplan.tx_time_for_contact(simtime, node1, node2, size)

    def is_lost(self, t : float, src: int, dst: int) -> bool:
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
            return self.contactplan.has_contact(t, src.id, dst.id)
    