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
topo.add_node(4)

topo.add_node(5)
topo.add_node(6)

topo.add_edge(1, 2)
topo.add_edge(2, 4)

topo.add_edge(1, 3)
topo.add_edge(3, 4)

topo.add_edge(1, 5)
topo.add_edge(5, 6)
topo.add_edge(6, 4)


# alternative: use the graph to calculate the routes
# and generate nodes from
nodes = pons.generate_nodes_from_graph(
    topo, router=pons.routing.StaticRouter(capacity=CAPACITY, graph=topo)
)
print(nodes)

config = {"movement_logger": False, "peers_logger": False}

ping_sender = pons.apps.PingApp(dst=4, interval=10, ttl=3600, size=100)
# interval = -1 means receive only and never send a ping, only pong
ping_receiver = pons.apps.PingApp(dst=1, interval=-1, ttl=3600, size=100)

nodes[0].router.apps = [ping_sender]
nodes[3].router.apps = [ping_receiver]

netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, [], config=config)

netsim.setup()
print(nodes[0].router.routes)

print(list(nx.all_shortest_paths(topo, 1, 4)))

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
