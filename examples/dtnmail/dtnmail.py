import random
import json
import sys
import logging
import os
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.parent.resolve()
try:
    import pons
except ImportError:
    sys.path.append(str(SCRIPT_DIR.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

import pons.routing

logger = logging.getLogger(__file__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
SIM_TIME = 300
NUM_NODES = 2
WORLD_SIZE = (1000, 1000)
# CAPACITY = 10000
CAPACITY = 0

SIM_TIME = 120
NUM_NODES = 3

mapping = {"n1": 1, "n2": 2, "n3": 3}
plan = pons.CoreContactPlan.from_file("3n.ccp", mapping=mapping)

random.seed(RANDOM_SEED)

net = pons.NetworkSettings("contactplan", range=0, contactplan=plan)

epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic, offset=1)
config = {"movement_logger": False, "peers_logger": False, "routing_logger": False}

udp1 = pons.apps.UdpGatewayApp(service=25, udp_out=("localhost", 10102), udp_in=10101)
udp2 = pons.apps.UdpGatewayApp(service=25, udp_out=("localhost", 10202), udp_in=10201)

netsim = pons.NetSim(
    SIM_TIME, nodes, config=config, realtime=True, factor=1
)
netsim.install_app("n1", udp1)
netsim.install_app("n3", udp2)

netsim.setup()

netsim.run()

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
