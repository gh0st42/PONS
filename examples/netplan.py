import random
import json
import sys
import networkx as nx
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


RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 3600
NUM_NODES = 4
CAPACITY = 10000
# CAPACITY = 0
random.seed(RANDOM_SEED)

print("Python Opportunistic Network Simulator")


# topo = nx.erdos_renyi_graph(NUM_NODES, 0.3)
topo = nx.watts_strogatz_graph(NUM_NODES, 2, 0.3)

plan = pons.net.NetworkPlan(topo)

print(plan.nodes())
print(plan.connections())

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

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

netsim = pons.NetSim(SIM_TIME, nodes, config=config, msggens=[msggenconfig])

netsim.setup()
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))

### second scenario

SIM_TIME = 120
NUM_NODES = 3

plan = pons.net.NetworkPlan.from_graphml(SCRIPT_DIR + "/data/3n-exported.graphml")
print(plan.nodes())
print(plan.connections())

plan2 = pons.CoreContactPlan.from_file(
    SCRIPT_DIR + "/data/3n-exported.ccm", plan.mapping
)
plan.set_contacts(plan2)

net2 = pons.NetworkSettings("networkplan2", range=0, contactplan=plan)

nodes = pons.generate_nodes(NUM_NODES, net=[net2], router=epidemic)
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
