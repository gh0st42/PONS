from .simulation import NetSim
from .node import generate_nodes, Node, NetworkSettings, Message, BROADCAST_ADDR
from .routing import Router, EpidemicRouter
from .mobility import Ns2Movement, OneMovement, OneMovementManager, generate_randomwaypoint_movement
from .apps import PingApp, App

import random

def message_event_generator(netsim, msggenconfig):
    """A message generator.
    """
    env = netsim.env
    counter = 0
    print("start message generator")
    while True:
        # check if interval is a tuple
        if isinstance(msggenconfig["interval"], tuple):
            yield env.timeout(random.randint(msggenconfig["interval"][0], msggenconfig["interval"][1]))
        else:
            yield env.timeout(msggenconfig["interval"])
        netsim.routing_stats["created"] += 1
        counter += 1
        src = random.randint(msggenconfig["src"][0], msggenconfig["src"][1]-1)
        dst = random.randint(msggenconfig["dst"][0], msggenconfig["dst"][1]-1)
        if isinstance(msggenconfig["size"], tuple):
            size = random.randint(
                msggenconfig["size"][0], msggenconfig["size"][1])
        else:
            size = msggenconfig["size"]
        if "ttl" not in msggenconfig:
            ttl = 3600
        elif isinstance(msggenconfig["ttl"], tuple):
            ttl = random.randint(
                msggenconfig["ttl"][0], msggenconfig["ttl"][1])
        else:
            ttl = msggenconfig["ttl"]
        msgid = "%s%d" % (msggenconfig["id"], counter)
        msg = Message(msgid, src,
                      dst, size,
                      env.now, ttl=ttl)
        netsim.nodes[src].router.add(msg)


def message_burst_generator(netsim, msggenconfig):
    """A message generator.
    """
    env = netsim.env
    counter = 0
    print("start message burst generator")
    while True:
        # check if interval is a tuple
        if isinstance(msggenconfig["interval"], tuple):
            yield env.timeout(random.randint(msggenconfig["interval"][0], msggenconfig["interval"][1]))
        else:
            yield env.timeout(msggenconfig["interval"])

        for src in range(msggenconfig["src"][0], msggenconfig["src"][1]):
            netsim.routing_stats["created"] += 1
            counter += 1
            dst = random.randint(
                msggenconfig["dst"][0], msggenconfig["dst"][1]-1)
            if isinstance(msggenconfig["size"], tuple):
                size = random.randint(
                    msggenconfig["size"][0], msggenconfig["size"][1])
            else:
                size = msggenconfig["size"]
            if "ttl" not in msggenconfig:
                ttl = 3600
            elif isinstance(msggenconfig["ttl"], tuple):
                ttl = random.randint(
                    msggenconfig["ttl"][0], msggenconfig["ttl"][1])
            else:
                ttl = msggenconfig["ttl"]
            msgid = "%s%d" % (msggenconfig["id"], counter)
            msg = Message(msgid, src,
                          dst, size,
                          env.now, ttl=ttl)
            # print("create message %s (%d->%d)" % (msgid, src, dst))
            netsim.nodes[src].router.add(msg)
