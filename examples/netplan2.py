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


RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
CAPACITY = 10000
# CAPACITY = 0
random.seed(RANDOM_SEED)

SIM_TIME = 120
NUM_NODES = 3

plan = pons.net.NetworkPlan.from_graphml(SCRIPT_DIR + "/data/3n-dyn-link.graphml")
print(plan.nodes())
print(plan.connections())

assert len(plan.nodes()) == 3
assert len(plan.connections()) == 1

net2 = pons.NetworkSettings("networkplan2", range=0, contactplan=plan)
