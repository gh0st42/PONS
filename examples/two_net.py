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
from math import floor, ceil

RANDOM_SEED = 42
SIM_TIME = 3600
NET_RANGE1 = 50
NET_RANGE2 = 100
NUM_NODES = 15
WORLD_SIZE = (1000, 1000)

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)

moves = pons.generate_randomwaypoint_movement(
    SIM_TIME, NUM_NODES, WORLD_SIZE[0], WORLD_SIZE[1], max_pause=60.0
)

net1 = pons.NetworkSettings("WIFI_SHORT", range=NET_RANGE1)
net2 = pons.NetworkSettings("WIFI_LONG", range=NET_RANGE2, loss=0.01)
epidemic = pons.routing.EpidemicRouter()

# first node group only part of net1
nodes1 = pons.generate_nodes(int(floor(NUM_NODES / 3)), net=[net1], router=epidemic)
# second node group only part of net2
nodes2 = pons.generate_nodes(
    int(floor(NUM_NODES / 3)), net=[net2], router=epidemic, offset=floor(NUM_NODES / 3)
)
# third node group part of both networks
nodes3 = pons.generate_nodes(
    int(ceil(NUM_NODES / 3)),
    net=[net1, net2],
    router=epidemic,
    offset=floor(NUM_NODES / 3) * 2,
)

nodes = nodes1 + nodes2 + nodes3

config = {"movement_logger": False, "peers_logger": False}

msggenconfig = {
    "type": "single",
    "interval": 30,
    "src": (0, NUM_NODES),
    "dst": (0, NUM_NODES),
    "size": 100,
    "id": "M",
}

netsim = pons.NetSim(
    SIM_TIME,
    nodes,
    world_size=WORLD_SIZE,
    movements=moves,
    config=config,
    msggens=[msggenconfig],
)

netsim.setup()


netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
