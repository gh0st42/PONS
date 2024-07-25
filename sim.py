import random
import json

# import cProfile

import pons
import pons.routing

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 3600 * 24
NET_RANGE = 50
NUM_NODES = 10
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000
# CAPACITY = 0

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)


moves = pons.generate_randomwaypoint_movement(
    SIM_TIME, NUM_NODES, WORLD_SIZE[0], WORLD_SIZE[1], max_pause=60.0
)

net = pons.NetworkSettings("WIFI_50m", range=NET_RANGE)
epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False, "event_logging": False}

msggenconfig = {
    "type": "single",
    "interval": 30,
    "src": (0, NUM_NODES),
    "dst": (0, NUM_NODES),
    "size": 100,
    "id": "M",
    "ttl": 3600,
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


# cProfile.run("netsim.run()")
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
