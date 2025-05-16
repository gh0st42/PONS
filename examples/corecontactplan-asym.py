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


RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000


SIM_TIME = 120
NUM_NODES = 3

plan = pons.CoreContactPlan.from_file(SCRIPT_DIR + "/data/3n-asym.ccm", symmetric=False)

print(plan)

random.seed(RANDOM_SEED)

net = pons.NetworkSettings("contactplan", range=0, contactplan=plan)

epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False}

msggenconfig1 = {
    "type": "single",
    "interval": 40,
    "src": 0,
    "dst": 2,
    "size": 100,
    "id": "M",
    "ttl": 3600,
}

msggenconfig2 = {
    "type": "single",
    "interval": 40,
    "src": 2,
    "dst": 0,
    "size": 100,
    "id": "M",
    "ttl": 3600,
}

print(
    "\nSending from 0 to 2 - unidirectional links, expected delivery of 1 out of 3 messages\n\n"
)
netsim = pons.NetSim(SIM_TIME, nodes, config=config, msggens=[msggenconfig1])

netsim.setup()

netsim.run()

print(json.dumps(netsim.routing_stats, indent=4))

print(
    "\nSending from 2 to 0 - unidirectional links, expected delivery of 0 out of 3 messages\n\n"
)
nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
netsim = pons.NetSim(SIM_TIME, nodes, config=config, msggens=[msggenconfig2])

netsim.setup()

netsim.run()

print(json.dumps(netsim.routing_stats, indent=4))
