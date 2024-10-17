import random
import json
import sys

from roverapp import RoverApp

import pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
print(SCRIPT_DIR)
try:
    import pons
except ImportError:
    print(SCRIPT_DIR.parent.parent.resolve())
    sys.path.append(str(SCRIPT_DIR.parent.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

import pons.routing

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 60 * 60
CAPACITY = 1_000_000
# CAPACITY = 0
PING_SIZE = 1_000

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)

plan = pons.net.NetworkPlan.from_graphml(SCRIPT_DIR + "/data/rover.graphml")

print(plan.nodes())
print(plan.connections())

plan2 = pons.CoreContactPlan.from_file(SCRIPT_DIR + "/data/rover.ccp", plan.mapping)
plan.set_contacts(plan2)

print(plan2.at(231.0))

# sys.exit(0)

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

# router = pons.routing.EpidemicRouter(capacity=CAPACITY)
# static routing needs to be passed the full contact graph with all POSSIBLE edges
router = pons.routing.StaticRouter(capacity=CAPACITY, graph=plan.full_graph)

nodes = pons.generate_nodes_from_graph(plan.G, router=router, contactplan=plan2)

config = {"movement_logger": False, "peers_logger": False, "event_logging": True}

ping_sender = RoverApp(dst=plan.mapping["moc1"], interval=10, ttl=3600, size=PING_SIZE)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=0, interval=-1, ttl=3600, size=PING_SIZE)

netsim = pons.NetSim(SIM_TIME, nodes, config=config, realtime=True)

netsim.install_app("rover1", ping_sender)
netsim.install_app("moc1", ping_receiver)

netsim.setup()


# cProfile.run("netsim.run()")
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
