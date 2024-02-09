PONS - Python Opportunistic Network Simulator
===

A simple DTN simulator in the style of [the ONE](https://github.com/akeranen/the-one).

Features:
- simple distance-based network simulation
- DTN routing algorithms
  - epidemic
  - spray & wait
  - first contact
  - direct delivery
  - PRoPHET
- mobility
  - random waypoint
  - external ONE movement
- contact plan connectivity model
  - ION DTN contact plans
  - [core contact plan}(https://github.com/gh0st42/ccm/)

## Requirements

- simpy >= 4.0
- plotting:
  - seaborn
  - pandas
  - matplotlib
  - numpy


## Example

```python
import random
import json

import pons
import pons.routing

RANDOM_SEED = 42
SIM_TIME = 3600*24
NET_RANGE = 50
NUM_NODES = 10
WORLD_SIZE = (3000, 3000)

# Setup and start the simulation
random.seed(RANDOM_SEED)

moves = pons.generate_randomwaypoint_movement(
    SIM_TIME, NUM_NODES, WORLD_SIZE[0], WORLD_SIZE[1], max_pause=60.0)

net = pons.NetworkSettings("NET1", range=NET_RANGE)
epidemic = pons.routing.EpidemicRouter()

nodes = pons.generate_nodes(NUM_NODES, net=[net], router=epidemic)
config = {"movement_logger": False, "peers_logger": False}

msggenconfig = {"type": "single", "interval": 30, 
  "src": (0, NUM_NODES), "dst": (0, NUM_NODES), 
  "size": 100, "id": "M"}

netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, moves,
                     config=config, msggens=[msggenconfig])

netsim.setup()

netsim.run()

# print results

print(json.dumps(netsim.net_stats, indent=4))
print(json.dumps(netsim.routing_stats, indent=4))
```

Run using `python3` or for improved performance use `pypy3`.
