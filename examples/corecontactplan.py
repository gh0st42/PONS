import random
import json
import sys

import pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
try:
    import pons
except ImportError:
    sys.path.append(str(SCRIPT_DIR.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

import pons.routing
from pons.net.plans import Contact, ContactPlan
from pons.net.plans.parser import read_ccp

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 120
NUM_NODES = 2
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000
# CAPACITY = 0

print("Python Opportunistic Network Simulator")

contacts = read_ccp(SCRIPT_DIR + "/data/simple.ccm", symmetric=True)
plan = ContactPlan(contacts, symmetric=True, loop=True)
print(plan.get_max_time())

random.seed(RANDOM_SEED)

net = pons.NetworkSettings("contactplan", range=0, contactplan=plan)

epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False}

msggenconfig = {
    "type": "single",
    "interval": 40,
    "src": (0, 1),
    "dst": (1, NUM_NODES),
    "size": 100,
    "id": "M",
    "ttl": 3600,
}

netsim = pons.NetSim(SIM_TIME, nodes, WORLD_SIZE, config=config, msggens=[msggenconfig])

netsim.setup()
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))

### second scenario

SIM_TIME = 120
NUM_NODES = 3

contacts = read_ccp(SCRIPT_DIR + "/data/3n.ccm", symmetric=True)
plan = ContactPlan(contacts, symmetric=True, loop=True)

random.seed(RANDOM_SEED)

net = pons.NetworkSettings("contactplan", range=0, contactplan=plan)

epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False}

msggenconfig = {
    "type": "single",
    "interval": 40,
    "src": (0, 1),
    "dst": (2, NUM_NODES),
    "size": 100,
    "id": "M",
    "ttl": 3600,
}

netsim = pons.NetSim(SIM_TIME, nodes, config=config, msggens=[msggenconfig])

netsim.setup()

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
