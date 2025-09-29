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
topo.add_node(0)
topo.add_node(1)
topo.add_node(2)
topo.add_node(3)
topo.add_edge(0, 1)
topo.add_edge(1, 2)
topo.add_edge(2, 3)

plan = pons.net.NetworkPlan(topo)

print(plan.nodes())
print(plan.connections())

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

# manually add routes
nodes = [
    pons.Node(0, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
    pons.Node(1, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
    pons.Node(2, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
    pons.Node(3, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
]

# node 0 can reach node 2 via node 1
# nodes[0].router.routes = [RouteEntry(dst=2, next_hop=1)]
# node 0 can reach node 3 via node 1
# nodes[0].router.routes.append(RouteEntry(dst=3, next_hop=1))

# add a default route via node 1
nodes[0].router.routes = [RouteEntry(dst="*", next_hop=1)]

# node 1 can reach node 2 directly
# node 1 can reach node 1 directly
# thus, no need to add routes for them
# nodes[1].router.routes = [RouteEntry(dst=2, next_hop=2)]
nodes[1].router.routes = [RouteEntry(dst=3, next_hop=2)]

# node 2 can reach node 0 via node 1
nodes[2].router.routes = [RouteEntry(dst=0, next_hop=1)]
# node 2 can reach node 3 directly

# node 3 can reach node 1 via node 2
nodes[3].router.routes = [RouteEntry(dst=1, next_hop=2)]
# node 3 can reach node 0 via node 2
nodes[3].router.routes.append(RouteEntry(dst=0, next_hop=2))

for n in nodes:
    print(n.name, n.router.routes)

config = {"movement_logger": False, "peers_logger": False, "real_scan": False}

ping_sender = pons.apps.PingApp(dst=2, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=0, interval=-1, ttl=3600, size=100)

nodes[0].router.apps = [ping_sender]
nodes[3].router.apps = [ping_receiver]

netsim = pons.NetSim(SIM_TIME, nodes, world_size=WORLD_SIZE, config=config)

netsim.setup()

for k, n in netsim.nodes.items():
    print(n.name, n.router.routes)

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
