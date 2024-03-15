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
topo.add_node(1)
topo.add_node(2)
topo.add_node(3)
topo.add_edge(1, 2)
topo.add_edge(2, 3)

plan = pons.net.NetworkPlan(topo)

print(plan.nodes())
print(plan.connections())

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)

# alternative: use the graph to calculate the routes
nodes = [
    pons.Node(
        1, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY, graph=topo)
    ),
    pons.Node(
        2, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY, graph=topo)
    ),
    pons.Node(
        3, net=[net], router=pons.routing.StaticRouter(capacity=CAPACITY, graph=topo)
    ),
]

config = {"movement_logger": False, "peers_logger": False}

ping_sender = pons.apps.PingApp(dst=3, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=1, interval=-1, ttl=3600, size=100)

nodes[0].router.apps = [ping_sender]
nodes[2].router.apps = [ping_receiver]

netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, [], config=config)

netsim.setup()
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
