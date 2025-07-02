import time
from typing import List, Dict, Optional, Tuple
from copy import deepcopy
import os
import signal
import logging

from pons.event_log import event_log, open_log, close_log, is_logging
import pons.event_log
from simpy import Environment
from simpy.rt import RealtimeEnvironment

import pons
from pons.node import Node
from pons.event_log import event_log

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

aborted = False


def printProgressBar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


class NetSim(object):
    """A network simulator."""

    env: Environment | RealtimeEnvironment

    def __init__(
        self,
        duration: int,
        nodes: List[Node],
        world_size: Tuple[float, float] = (0, 0),
        movements: Optional[list] = None,
        msggens: Optional[list] = None,
        config: Optional[dict] = None,
        name_to_id_map: Optional[Dict[str, int]] = None,
        realtime: bool = False,
        factor: float = 1,
        strict: bool = True,
    ):
        if realtime:
            self.env = RealtimeEnvironment(factor=factor, strict=strict)
        else:
            self.env = Environment()

        self.realtime = realtime

        self.duration = duration
        if "SIM_DURATION" in os.environ:
            logger.info(
                "ENV SIM_DURATION found! Using duration: %s" % os.getenv("SIM_DURATION")
            )
            self.duration = int(os.getenv("SIM_DURATION"))

        # convert list from Node to dict with id as key
        self.nodes = {n.node_id: n for n in nodes}
        # self.nodes = nodes
        self.world = world_size
        if movements is None:
            movements = []
        self.movements = movements
        if msggens is None:
            msggens = []
        self.msggens = msggens
        if config is None:
            config = {}
        self.config = config

        self.do_actual_scan = config.get("real_scan", False)

        self.net_stats = {"tx": 0, "rx": 0, "drop": 0, "loss": 0}
        self.routing_stats = {
            "created": 0,
            "delivered": 0,
            "dropped": 0,
            "hops": 0,
            "latency": 0.0,
            "started": 0,
            "relayed": 0,
            "removed": 0,
            "aborted": 0,
            "dups": 0,
            "latency_avg": 0.0,
            "delivery_prob": 0.0,
            "hops_avg": 0.0,
            "overhead_ratio": 0.0,
        }
        self.router_stats = {}

        if name_to_id_map is None:
            name_to_id_map = {}
        self.name_to_id_map = name_to_id_map
        if len(self.name_to_id_map) == 0:
            for n in self.nodes.values():
                self.name_to_id_map[n.name] = n.node_id

        if self.world == (0, 0):
            self.world = (
                max(n.x for n in self.nodes.values()) + 50,
                max(n.y for n in self.nodes.values()) + 50,
            )

        self.mover = pons.OneMovementManager(self.env, self.nodes, self.movements)

    def get_id_by_name(self, name):
        return self.name_to_id_map.get(name, -1)

    def start_movement_logger(self, interval=1.0):
        """Start a movement logger."""
        logger.debug("Starting movement logger...")
        while True:
            yield self.env.timeout(interval)
            logger.debug("Time: %d", self.env.now)
            for node in self.nodes:
                logger.debug("Node: %s", node)

    def start_peers_logger(self, interval=1.0):
        """Start a peers logger."""
        logger.debug("Starting peers logger...")
        while True:
            yield self.env.timeout(interval)
            logger.debug("Time: %d", self.env.now)
            for node in self.nodes.values():
                logger.debug("Node: %s", node.neighbors)

    def setup(self):
        logger.info("Initializing simulation: %s", self.config)

        if self.movements is not None and len(self.movements) > 0:
            logger.debug("Starting movement manager...")
            self.mover.start()

        if self.config is not None:
            if self.config.get("movement_logger", True):
                self.env.process(self.start_movement_logger())

            if self.config.get("peers_logger", True):
                self.env.process(self.start_peers_logger())

            if "LOG_FILE" in os.environ:
                logger.info(
                    "ENV LOG_FILE found! Activating event logging using log file: %s"
                    % os.getenv("LOG_FILE"),
                )
                self.config["event_logging"] = True

            if self.config.get("event_logging", False):
                log_file = os.getenv("LOG_FILE", "/tmp/events.log")
                # if OS is windows replace /tmp/ with C:/temp/
                if os.name == "nt":
                    log_file = log_file.replace("/tmp/", "C:/temp/")

                open_log(log_file)

            pons.event_log.event_filter = self.config.get("event_filter", [])

        for n in self.nodes.values():
            # print("-> start node %d w/ %d apps" % (n.id, len(n.apps)))
            n.start(self)

        if self.msggens is not None:
            for msggen in self.msggens:
                if (
                    "type" not in msggen.keys()
                    or msggen["type"] is None
                    or msggen["type"] == "single"
                ):
                    self.env.process(pons.message_event_generator(self, msggen))
                elif msggen["type"] == "burst":
                    self.env.process(pons.message_burst_generator(self, msggen))
                else:
                    raise Exception("unknown message generator type")

        logger.debug("Nodes: %s", self.nodes)
        for n in self.nodes.values():
            n.calc_neighbors(0, self.nodes.values())

    def using_contactplan(self):
        for n in self.nodes.values():
            for net in n.net.values():
                if net.contactplan is not None:
                    return True
        return False

    def install_app(self, node, app):
        if isinstance(node, str):
            node = self.get_id_by_name(node)

        self.nodes[node].router.apps.append(deepcopy(app))

    def contact_logger(self, contactplan):
        """Start a contact logger."""
        if not is_logging():
            return
        
        logger.debug("start contact logger: %s", type(contactplan))
        if contactplan is None:
            logger.warning("No contact plan")
            return
        initial_events = contactplan.at(0)
        if len(initial_events) != 0:
            for e in initial_events:
                if e.timespan[0] == 0:
                    event_log(0, "LINK", {"event": "UP", "nodes": e.nodes})

        next_event = contactplan.next_event(0)
        if next_event is None:
            logger.warning("No events in contact plan")
            return

        total = 0
        while True:
            yield self.env.timeout(next_event)
            total += next_event
            events = contactplan.at(total)
            # print(len(events), "events at", total, ":", events)
            for e in events:
                if e.timespan[0] == total:
                    event_log(total, "LINK", {"event": "UP", "nodes": e.nodes})
                if e.timespan[1] == total:
                    event_log(total, "LINK", {"event": "DOWN", "nodes": e.nodes})

            next_event = contactplan.next_event(total)
            if next_event is None or next_event > self.duration:
                break
            next_event -= total

    def run(self):
        logger.info("== running simulation for %d seconds ==" % self.duration)

        # install signal handler to stop simulation if ctrl-c is pressed
        def signal_handler(sig, frame):
            global aborted
            logger.info("Stopping simulation...")
            aborted = True

        signal.signal(signal.SIGINT, signal_handler)

        all_contactplans = set()
        for n in self.nodes.values():
            event_log(
                0,
                "CONFIG",
                {
                    "event": "START",
                    "id": n.node_id,
                    "name": n.name,
                    "x": n.x,
                    "y": n.y,
                    "capacity": n.router.capacity,
                    "used": n.router.used,
                },
            )
            for net in n.net.values():
                net.start(self)
                if net.contactplan is not None:
                    all_contactplans.add(net.contactplan)


        for cp in all_contactplans:
            self.env.process(self.contact_logger(cp))
        
        logger.debug("Global number of unique contact plans: %d", len(all_contactplans))

        start_real = time.time()
        last_real = start_real
        last_sim = 0.0

        if self.using_contactplan():
            contacts = set()
            for n in self.nodes.values():
                n.add_all_neighbors(self.env.now, self.nodes.values())
                for net in n.net.values():
                    contacts.update(net.contactplan.fixed_links())

                # print(
                #     "node %f %d: %d %d"
                #     % (
                #         self.env.now,
                #         n.id,
                #         len(n.net[list(n.net.keys())[0]].contactplan.at(0)),
                #         len(n.neighbors[list(n.neighbors.keys())[0]]),
                #     )
                # )
            logger.debug(
                "global number of unique contacts: %d %s", len(contacts), contacts
            )
            for c in contacts:
                event_log(
                    0,
                    "LINK",
                    {
                        "event": "SET",
                        "node1": c[0],
                        "node2": c[1],
                    },
                )

        else:
            now_sim = self.env.now
            for n in self.nodes.values():
                n.calc_neighbors(now_sim, self.nodes.values())

        print("")
        while self.env.now < self.duration + 1.0 and not aborted:
            now_sim = self.env.now
            step_size = 5.0
            if self.realtime:
                step_size = 0.01
            next_stop = min(self.duration + 1.0, now_sim + step_size)
            self.env.run(until=next_stop)

            now_real = time.time()
            diff = now_real - last_real
            if diff > 60:
                rate = (now_sim - last_sim) / diff
                print(
                    "\n\nsimulated %d seconds in %d seconds (%.2f x real time)"
                    % (now_sim - last_sim, diff, rate)
                )
                print(
                    "real: %f, sim: %d rate: %.02f steps/s"
                    % (now_real - start_real, now_sim, rate)
                )
                print()
                last_real = now_real
                last_sim = now_sim
            printProgressBar(
                now_sim,
                self.duration,
                prefix="Progress:",
                suffix="Complete",
                length=50,
            )

        # self.env.run(until=self.duration)
        now_real = time.time()
        diff = now_real - start_real
        now_sim = self.env.now

        if diff > 0:
            rate = (now_sim) / diff
        else:
            rate = 0.0

        print("\n\n")
        if aborted:
            logger.warning("simulation aborted")
        else:
            logger.info("simulation finished")
        logger.info(
            "simulated %d seconds in %.02f seconds (%.2f x real time)"
            % (now_sim, diff, rate)
        )
        logger.info("real: %f, sim: %d rate: %.02f steps/s" % (diff, now_sim, rate))

        if self.routing_stats["delivered"] > 0:
            self.routing_stats["latency_avg"] = (
                self.routing_stats["latency"] / self.routing_stats["delivered"]
            )
            self.routing_stats["hops_avg"] = (
                self.routing_stats["hops"] / self.routing_stats["delivered"]
            )
            self.routing_stats["overhead_ratio"] = (
                self.routing_stats["relayed"] - self.routing_stats["delivered"]
            ) / self.routing_stats["delivered"]
        if self.routing_stats["created"] > 0:
            self.routing_stats["delivery_prob"] = (
                self.routing_stats["delivered"] / self.routing_stats["created"]
            )
        else:
            self.routing_stats["delivery_prob"] = 0.0

        # delete entry "hops" and "latency" from routing_stats as they are only used for calculating the average
        del self.routing_stats["hops"]
        del self.routing_stats["latency"]

        event_log(
            now_sim,
            "STATS",
            {
                "event": "ABORT" if aborted else "END",
                "duration": now_sim,
                "real_duration": diff,
                "rate": rate,
                "net": self.net_stats,
                "routing": self.routing_stats,
            },
        )

        close_log()
