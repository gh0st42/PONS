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
SIM_TIME = 60 * 60
NUM_NODES = 2
WORLD_SIZE = (1000, 1000)
CAPACITY = 1_000_000
# CAPACITY = 0
PING_SIZE = 100_000

# Setup and start the simulation
print("Python Opportunistic Network Simulator")
random.seed(RANDOM_SEED)

# a range of 0 means infinite range
# net = pons.NetworkSettings("LAN", range=0, bandwidth=250, delay=0.01, loss=0.0)
net = pons.NetworkSettings("LAN", range=0, bandwidth=1000000, delay=0.00, loss=0.0)
epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY, scan_interval=30.0)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False, "event_logging": True}
moves = pons.generate_randomwaypoint_movement(
    SIM_TIME, NUM_NODES, WORLD_SIZE[0], WORLD_SIZE[1]
)

ping_sender = pons.apps.PingApp(dst=1, interval=10, ttl=3600, size=PING_SIZE)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=0, interval=-1, ttl=3600, size=PING_SIZE)

nodes[0].router.apps = [ping_sender]
nodes[1].router.apps = [ping_receiver]

netsim = pons.NetSim(
    SIM_TIME, nodes, world_size=WORLD_SIZE, config=config, realtime=False
)

netsim.setup()


# cProfile.run("netsim.run()")
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
