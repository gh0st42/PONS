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
from pons.routing.static import RouteEntry


RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 360
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000
# CAPACITY = 0
random.seed(RANDOM_SEED)


topo = nx.graph.Graph()
topo.add_node(1)
topo.add_node(2)
topo.add_node(3)
topo.add_edge(1, 2)
topo.add_edge(2, 3)

plan = pons.net.NetworkPlan(topo)
net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

# alternative: use the graph to calculate the routes
# and generate nodes from
nodes = pons.generate_nodes_from_graph(
    topo,
    router=pons.routing.StaticRouter(capacity=CAPACITY, graph=topo),
    net=[net],
)

config = {"movement_logger": False, "peers_logger": False, "event_logging": True}

netsim = pons.NetSim(SIM_TIME, nodes, world_size=WORLD_SIZE, config=config)

ping_sender = pons.apps.PingApp(dst=3, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=1, interval=-1, ttl=3600, size=100)

netsim.install_app(1, ping_sender)
netsim.install_app(3, ping_receiver)

netsim.setup()
for n in nodes:
    print(n, n.router.routes)

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
