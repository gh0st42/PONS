import random
import json
import sys
import networkx as nx
import sys


sys.path.append("..")

import pons
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
topo.add_edge(0, 1)
topo.add_edge(1, 2)

plan = pons.net.NetworkPlan(topo)

print(plan.nodes())
print(plan.connections())

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

# router = pons.routing.StaticRouter(capacity=CAPACITY)

nodes = [
    pons.Node(0, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
    pons.Node(1, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
    pons.Node(2, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY)),
]

# node 0 can reach node 2 via node 1
nodes[0].router.routes = [RouteEntry(dst=2, next_hop=1)]
# node 1 can reach node 2 directly
# node 1 can reach node 1 directly
# thus, no need to add routes for them
# nodes[1].router.routes = [RouteEntry(dst=2, next_hop=2)]
# node 2 can reach node 0 via node 1
nodes[2].router.routes = [RouteEntry(dst=0, next_hop=1)]

config = {"movement_logger": False, "peers_logger": False}

ping_sender = pons.apps.PingApp(dst=2, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=0, interval=-1, ttl=3600, size=100)

nodes[0].router.apps = [ping_sender]
nodes[2].router.apps = [ping_receiver]

netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, [], config=config, msggens=[])

netsim.setup()
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
