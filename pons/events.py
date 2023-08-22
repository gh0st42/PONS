from enum import Enum
from typing import List, Dict, Set
import pons
import simpy


class EventType(Enum):
    RECEIVED = 0
    DELIVERED = 1
    CREATED = 2
    CONNECTION_UP = 3
    CONNECTION_DOWN = 4
    DROPPED = 5
    RELAY_STARTED = 6


class Event:
    """Simulation Events"""

    def __init__(self, type: EventType, node: int, from_node: int, message: "pons.Message", time: float):
        self.type: EventType = type
        self.node: int = node
        self.from_node: int = from_node
        self.message: pons.Message = message
        self.time: float = time

    def __str__(self):
        if self.type == EventType.RECEIVED:
            return f"{self.time}: Message relayed {self.from_node} <-> {self.node} {self.message.id}"
        if self.type == EventType.DELIVERED:
            return f"{self.time}: Message delivered {self.from_node} <-> {self.node} {self.message.id}"
        if self.type == EventType.CREATED:
            return f"{self.time}: Message created {self.node} {self.message.id}"
        if self.type == EventType.CONNECTION_UP:
            return f"{self.time}: Connection UP {self.node} <-> {self.from_node}"
        if self.type == EventType.CONNECTION_DOWN:
            return f"{self.time}: Connection DOWN {self.node} <-> {self.from_node}"
        if self.type == EventType.DROPPED:
            return f"{self.time}: Message dropped {self.node} {self.message.id}"
        if self.type == EventType.RELAY_STARTED:
            return f"{self.time}: Message relay started {self.node} {self.message.id}"

        return ""

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        if other.type != self.type:
            return False
        if other.time != self.time:
            return False
        if self.type in [EventType.RECEIVED, EventType.DELIVERED]:
            return self.node == other.node and self.from_node == other.from_node and self.message == other.message
        if self.type in [EventType.CREATED, EventType.DROPPED, EventType.RELAY_STARTED]:
            return self.node == other.node and self.message == other.message
        return self.node == other.node and self.from_node == other.from_node or self.node == other.from_node and self.from_node == other.node

    def __hash__(self):
        return self.type.value + self.node + self.from_node + hash(self.message) + int(self.time)


class EventManager:
    def __init__(self, env: simpy.Environment, nodes: "List[pons.Node]"):
        self._env: simpy.Environment = env
        self.events: Set[Event] = set()
        self._last_peers: Dict[int, Set[int]] = {node.id: set() for node in nodes}
        self._current_peers: Dict[int, Set[int]] = {node.id: set() for node in nodes}

    def on_message_received(self, node: int, from_node: int, msg: "pons.Message"):
        self.events.add(Event(EventType.RECEIVED, node, from_node, msg, self._env.now))

    def on_message_delivered(self, node: int, from_node: int, msg: "pons.Message"):
        self.events.add(Event(EventType.DELIVERED, node, from_node, msg, self._env.now))

    def on_message_created(self, node: int, msg: "pons.Message"):
        self.events.add(Event(EventType.CREATED, node, node, msg, self._env.now))

    def on_message_dropped(self, node: int, msg: "pons.Message"):
        self.events.add(Event(EventType.DROPPED, node, node, msg, self._env.now))

    def on_peer_discovery(self, node1: int, node2: int):
        if node2 not in self._last_peers[node1] and node1 not in self._last_peers[node2]:
            self.events.add(Event(EventType.CONNECTION_UP, node1, node2, None, self._env.now))
        self._current_peers[node1].add(node2)
        self._current_peers[node2].add(node1)

    def on_before_scan(self, node: int):
        lost_peers = [peer for peer in self._last_peers[node] if peer not in self._current_peers[node]]
        events = [Event(EventType.CONNECTION_DOWN, node, peer, None, self._env.now) for peer in lost_peers]
        for event in events:
            self.events.add(event)
        self._last_peers[node] = self._current_peers[node].copy()
        self._current_peers[node].clear()
        for peer in lost_peers:
            if node in self._current_peers[peer]:
                self._current_peers[peer].remove(node)
