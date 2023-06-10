from typing import List

import simpy
import time
import pons
from enum import Enum


class EventType(Enum):
    SENT = 0


#class Event:
#    """Simulation Events"""
#    def __init__(self, type: EventType, node1: pons.Node, node2: pons.Node, message: pons.Message):
#        self.type: EventType = type
#        self.node1: pons.Node = node1
#        self.node2: pons.Node = node2
#        self.message: pons.Message = message
#
#    def __str__(self):
#        if self.type == EventType.SENT:
#            return f"{self.node1} sent {self.message} to {self.node2}"
#        raise NotImplementedError(f"{self.type} can not be converted to str")


class NetSim(object):
    """A network simulator.
    """

    def __init__(self, duration, world, nodes, movements=[], msggens=None, config=None):
        self.env = simpy.Environment()
        self.duration = duration
        self.nodes = nodes
        self.world = world
        self.movements = movements
        self.msggens = msggens
        self.config = config

        self.net_stats = {'tx': 0, 'rx': 0, 'drop': 0, 'loss': 0}
        self.routing_stats = {'created': 0, 'delivered': 0, 'dropped': 0, 'hops': 0,
                              'latency': 0.0, 'started': 0, 'relayed': 0, 'removed': 0, 'aborted': 0, 'dups': 0,
                              'latency_avg': 0.0, 'delivery_prob': 0.0, 'hops_avg': 0.0, 'overhead_ratio': 0.0}
        self.router_stats = {}
        #self.events: List[Event] = []

        self.mover = pons.OneMovementManager(
            self.env, self.nodes, self.movements)

    def start_movement_logger(self, interval=1.0):
        """Start a movement logger.
        """
        print("start movement logger1")
        while True:
            yield self.env.timeout(interval)
            print("time: %d" % self.env.now)
            for node in self.nodes:
                print(node)

    def start_peers_logger(self, interval=1.0):
        """Start a peers logger.
        """
        print("start peers logger1")
        while True:
            yield self.env.timeout(interval)
            print("time: %d" % self.env.now)
            for node in self.nodes:
                print(node.neighbors)

    def setup(self):
        print("initialize simulation")

        if self.movements is not None and len(self.movements) > 0:
            print("-> start movement manager")
            self.mover.start()

        if self.config is not None and self.config.get("movement_logger", True):
            self.env.process(self.start_movement_logger())

        if self.config is not None and self.config.get("peers_logger", True):
            self.env.process(self.start_peers_logger())

        for n in self.nodes:
            n.start(self)

        if self.msggens is not None:
            for msggen in self.msggens:
                if "type" not in msggen.keys() or msggen["type"] is None or msggen["type"] == "single":
                    self.env.process(
                        pons.message_event_generator(self, msggen))
                elif msggen["type"] == "burst":
                    self.env.process(
                        pons.message_burst_generator(self, msggen))
                else:
                    raise Exception("unknown message generator type")

    def run(self):
        print("run simulation")
        start_real = time.time()
        last_real = start_real
        last_sim = 0.0
        while self.env.now < self.duration + 1.0:
            # self.env.run(until=self.duration)
            now_sim = self.env.now
            next_stop = min(self.duration + 1.0, now_sim + 5.0)
            self.env.run(until=next_stop)
            now_real = time.time()
            diff = now_real - last_real
            if diff > 60:
                rate = (now_sim - last_sim) / diff
                print("simulated %d seconds in %d seconds (%.2f x real time)" %
                      (now_sim - last_sim, diff, rate))
                print("real: %f, sim: %d rate: %.02f steps/s" %
                      (now_real - start_real, now_sim, rate))
                last_real = now_real
                last_sim = now_sim

        # self.env.run(until=self.duration)
        now_real = time.time()
        diff = now_real - start_real
        now_sim = self.env.now
        rate = (now_sim) / diff

        print("\nsimulation finished")
        print("simulated %d seconds in %.02f seconds (%.2f x real time)" %
              (now_sim, diff, rate))
        print("real: %f, sim: %d rate: %.02f steps/s" %
              (diff, now_sim, rate))

        if self.routing_stats["delivered"] > 0:
            self.routing_stats["latency_avg"] = self.routing_stats["latency"] / \
                self.routing_stats["delivered"]
            self.routing_stats["hops_avg"] = self.routing_stats["hops"] / \
                self.routing_stats["delivered"]
            self.routing_stats["overhead_ratio"] = (self.routing_stats["relayed"] - self.routing_stats["delivered"]) / \
                self.routing_stats["delivered"]

        self.routing_stats["delivery_prob"] = self.routing_stats["delivered"] / \
            self.routing_stats["created"]

        # delete entry "hops" and "latency" from routing_stats as they are only used for calculating the average
        del self.routing_stats["hops"]
        del self.routing_stats["latency"]
