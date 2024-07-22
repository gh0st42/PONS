import random
import math
from typing import Dict
from dataclasses import dataclass

from pons.node import Node
from pons.simulation import event_log


@dataclass
class OneMovement(object):
    """A The ONE movement file."""

    def __init__(
        self, duration: float, num_nodes: int, width: int, height: int, moves=None
    ):
        self.duration = duration
        self.num_nodes = num_nodes
        self.width = width
        self.height = height
        if moves is None:
            moves = []
        self.moves = moves

    def __str__(self):
        return "OneMovement(%d, %d, %d, %d, %d)" % (
            self.duration,
            self.num_nodes,
            self.width,
            self.height,
            len(self.moves),
        )

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as f:
            lines = f.readlines()
            first_line = lines[0].split()
            duration = float(first_line[1])
            num_nodes = 0
            width = float(first_line[3])
            height = float(first_line[5])
            moves = []
            for line in lines[1:]:
                time, node_id, x, y = line.split()
                time = float(time)
                node_id = int(node_id)
                num_nodes = max(num_nodes, node_id + 1)
                x = float(x)
                y = float(y)
                z = 0.0
                moves.append((time, node_id, x, y, z))
            return cls(duration, num_nodes, width, height, moves)


class OneMovementManager(object):
    """A The ONE movement manager."""

    def __init__(self, env, nodes: Dict[int, Node], moves):
        self.env = env
        self.nodes = nodes
        self.moves = moves
        self.move_idx = 0

    def start(self):
        if self.move_idx <= len(self.moves):
            time = 0.0
            while time == 0.0:
                time, node_id, x, y, z = self.moves[self.move_idx]
                self.move_idx += 1
                node = self.nodes[node_id]
                node.x = x
                node.y = y
                node.z = z

            for n in self.nodes.values():
                n.calc_neighbors(time, self.nodes.values())
            self.env.process(self.move_next(time, node_id, x, y, z))

    def move_next(self, time, node_id, x, y, z):
        yield self.env.timeout(time - self.env.now)
        node = self.nodes[node_id]
        node.x = x
        node.y = y
        node.z = z
        event_log(time, "MOVE", {"event": "SET", "id": node_id, "x": x, "y": y, "z": z})

        # move all nodes with same timestamp
        while self.move_idx < len(self.moves):
            next_time, node_id, x, y, z = self.moves[self.move_idx]
            self.move_idx += 1

            if time == next_time:
                node = self.nodes[node_id]
                node.x = x
                node.y = y
                node.z = z
                event_log(
                    time,
                    "MOVE",
                    {"event": "SET", "id": node_id, "x": x, "y": y, "z": z},
                )
            else:
                self.env.process(self.move_next(next_time, node_id, x, y, z))
                break

        now = self.env.now
        for n in self.nodes.values():
            n.calc_neighbors(now, self.nodes.values())


def generate_randomwaypoint_movement(
    duration,
    num_nodes,
    width,
    height,
    min_speed=1.0,
    max_speed=5.0,
    min_pause=0,
    max_pause=120,
):
    """Generate random waypoint movement for a number of nodes."""
    moves = []
    for i in range(num_nodes):
        cur_time = 0.0
        x = random.randint(0, width)
        y = random.randint(0, height)
        z = 0.0
        moves.append((cur_time, i, x, y, z))
        while cur_time < duration:
            way_x = random.randint(0, width)
            way_y = random.randint(0, height)
            speed = random.random() * (max_speed - min_speed) + min_speed
            pause = random.randint(min_pause, max_pause)
            cur_time += pause
            dist = math.sqrt((way_x - x) ** 2 + (way_y - y) ** 2)
            time = dist / speed
            step_x = (way_x - x) / time
            step_y = (way_y - y) / time
            for j in range(int(time)):
                if cur_time + j >= duration:
                    break
                cur_time += 1
                x += step_x
                y += step_y
                moves.append((cur_time, i, x, y, z))

    # sort moves by time and node id
    moves.sort(key=lambda x: (x[0], x[1]))

    return moves
