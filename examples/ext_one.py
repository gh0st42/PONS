import random
import math
import time
import simpy
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
SIM_TIME = 3600
NET_RANGE = 100
NUM_NODES = 17
WORLD_SIZE = (1000, 1000)

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)

moves = pons.OneMovement.from_file(SCRIPT_DIR + "/data/movements.one")

print(moves)

net = pons.NetworkSettings("WIFI", range=NET_RANGE)
epidemic = pons.routing.EpidemicRouter()

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False, "event_logging": True}

msggenconfig = {
    "type": "burst",
    "interval": 20.0,
    "src": (5, 15),
    "dst": (16, 17),
    "size": (80, 120),
    "id": "M",
}

netsim = pons.NetSim(
    SIM_TIME,
    nodes,
    world_size=WORLD_SIZE,
    movements=moves.moves,
    config=config,
    msggens=[msggenconfig],
)

netsim.setup()

# netsim.env.process(pons.message_burst_generator(netsim, msggenconfig))
# netsim.env.process(pons.message_event_generator(netsim, msggenconfig))

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
