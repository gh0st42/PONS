import random
import json
import sys

sys.path.append("..")

# import cProfile

import pons
import pons.routing

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 60 * 60
NUM_NODES = 2
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000
# CAPACITY = 0

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)

# a range of 0 means infinite range
net = pons.NetworkSettings("LAN", range=0, bandwidth=250, delay=0.01, loss=0.0)
epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY, scan_interval=30.0)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False}
moves = pons.generate_randomwaypoint_movement(
    SIM_TIME, NUM_NODES, WORLD_SIZE[0], WORLD_SIZE[1]
)

ping_sender = pons.apps.PingApp(dst=1, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=0, interval=-1, ttl=3600, size=100)

nodes[0].router.apps = [ping_sender]
nodes[1].router.apps = [ping_receiver]


# msggenconfig = {"type": "single", "interval": 30, "src": [0,1], "dst": [1,2], "size": 100, "id": "M", "ttl": 3600}

netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, None, config=config)

netsim.setup()

# m = pons.Message("MSG1", 1, 2, 100, 0)
# pons.delayed_execution(netsim.env, 0, nodes[0].router.add(m))
# cProfile.run("netsim.run()")
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
