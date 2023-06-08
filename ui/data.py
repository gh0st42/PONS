import random
from typing import Dict

import pandas as pd

import pons

RANDOM_SEED = 42
# SIM_TIME = 3600*24*7
# SIM_TIME = 3600*24
SIM_TIME = 3600
NET_RANGE = 50
WORLD_SIZE = (1000, 1000)
CAPACITY = 10000


random.seed(RANDOM_SEED)


def generate_movement(settings: Dict):
    return pons.generate_randomwaypoint_movement(SIM_TIME,
                                                 settings["NUM_NODES"],
                                                 WORLD_SIZE[0],
                                                 WORLD_SIZE[1],
                                                 max_pause=60.0)


def simulate(moves, settings: Dict):
    num_nodes = settings["NUM_NODES"]
    net = pons.NetworkSettings("WIFI_50m", range=NET_RANGE)
    epidemic = pons.routing.EpidemicRouter(capacity=CAPACITY)

    nodes = pons.generate_nodes(
        num_nodes, net=[net], router=epidemic)
    config = {"movement_logger": False, "peers_logger": False}

    msggenconfig = {"type": "single", "interval": 30, "src": (
        0, num_nodes), "dst": (0, num_nodes), "size": 100, "id": "M", "ttl": 3600}

    netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, moves,
                         config=config, msggens=[msggenconfig])


def get_dataframe(settings: Dict):
    data = generate_movement(settings)
    missing = [(float(t), n) for t in range(SIM_TIME) for n in range(settings["NUM_NODES"])]
    d = {}
    index = 0
    result = {"time": {}, "node": {}, "x": {}, "y": {}, "range": {}}
    for entry in data:
        time = entry[0]
        node = entry[1]
        x = entry[2]
        y = entry[3]
        if time in d:
            d[time][node] = (x, y)
        else:
            d[time] = {node: (x, y)}
        result["time"][index] = time
        result["node"][index] = node
        result["x"][index] = x
        result["y"][index] = y
        result["range"][index] = NET_RANGE
        index += 1
        missing.remove((time, node))

    missing = sorted(missing, key=lambda m: m[0])

    for (time, node) in missing:
        value = d[time - 1][node]
        if time not in d:
            d[time] = {}
        d[time][node] = value
        result["time"][index] = time
        result["node"][index] = node
        result["x"][index] = value[0]
        result["y"][index] = value[1]
        result["range"][index] = NET_RANGE
        index += 1

    return pd.DataFrame.from_dict(result)