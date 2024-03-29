import random
import json
import sys
import networkx as nx
import sys

sys.path.append("..")

# import cProfile

import pons
import pons.routing


RANDOM_SEED = 42
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000
# CAPACITY = 0
random.seed(RANDOM_SEED)


SIM_TIME = 120
NUM_NODES = 3

# 3n exported is mapped from node IDs 0 to 2
# plan = pons.net.NetworkPlan.from_graphml("data/3n-exported.graphml")

# 3n netedit is mapped from node IDs 1 to 3
plan = pons.net.NetworkPlan.from_graphml("data/3n-netedit.graphml")

print(plan.nodes())
print(plan.connections())

plan2 = pons.CoreContactPlan.from_file("data/3n-exported.ccm", plan.mapping)
plan.set_contacts(plan2)

net = pons.NetworkSettings("networkplan", range=0, contactplan=plan)
# epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

# static routing needs to be passed the full contact graph with all POSSIBLE edges
static = pons.routing.StaticRouter(capacity=CAPACITY, graph=plan.full_graph)

nodes = pons.generate_nodes_from_graph(plan.G, net=[net], router=static)
config = {"movement_logger": False, "peers_logger": False}

msggenconfig = {
    "type": "single",
    "interval": 40,
    "src": 1,
    "dst": 3,
    "size": 100,
    "id": "M",
    "ttl": 3600,
}


netsim = pons.NetSim(
    SIM_TIME, WORLD_SIZE, nodes, [], config=config, msggens=[msggenconfig]
)

netsim.setup()
netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
