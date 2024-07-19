#!/usr/bin/env python3

import sys
import networkx as nx
from PIL import Image, ImageDraw
import argparse

try:
    import pons
except ImportError:
    sys.path.append("../../")

from pons.net.contactplan import CoreContactPlan
from pons.net.netplan import NetworkPlan

parser = argparse.ArgumentParser(description="Visualize a network replay")
parser.add_argument("contacts", type=str, help="The network contacts file")
parser.add_argument(
    "-o", "--output", type=str, help="The output image file", required=True
)
parser.add_argument(
    "-s", "--step-size", type=int, help="Step size in seconds", default=100
)
parser.add_argument("-g", "--graph", type=str, help="Input graphml file", required=True)

args = parser.parse_args()

print(args.graph)
g = nx.read_graphml(args.graph, node_type=int)

max_x = 0
max_y = 0
node_map = {}

for node in g.nodes.data():
    print(node)
    x = int(node[1]["x"])
    y = int(node[1]["y"])
    max_x = max(max_x, x)
    max_y = max(max_y, y)
    node_map[node[1]["name"]] = node[0]

img_size = (max_x + 50, max_y + 50)
print(max_x + 50, max_y + 50)

print(g.edges.data())
print(node_map)

contacts = CoreContactPlan.from_file(args.contacts, node_map)
print(contacts)
# find highest time
max_time = contacts.get_max_time()
print("Max time: %d" % max_time)
# sys.exit(0)
plan = NetworkPlan(g, contacts)
print(plan)

frames = []


def draw_progress(draw, x, y, progress, max_width):
    line_length = int(progress * max_width)
    draw.line((x, y, x + max_width, y), fill="lightgrey", width=4)
    draw.line((x, y, x + line_length, y), fill="black", width=4)
    # draw.text((x, y), "Time: %ds" % cur_time, fill="black")
    # draw.text((x, y + 20), "Max time: %ds" % max_time, fill="black")


def draw_node(img, x, y, name=""):
    if name:
        img.text((x + 6, y + 6), name, fill="black")
    img.circle((x, y), 8, fill="blue")


def draw_network(g, connections=[]):
    image = Image.new("RGB", (max_x + 50, max_y + 50), "white")
    draw = ImageDraw.Draw(image)

    # draw the links
    for edge in connections:
        x1 = int(g.nodes[edge[0]]["x"])
        y1 = int(g.nodes[edge[0]]["y"])
        x2 = int(g.nodes[edge[1]]["x"])
        y2 = int(g.nodes[edge[1]]["y"])
        draw.line((x1, y1, x2, y2), fill="black")

    # draw the nodes
    for node in g.nodes.data():
        x = int(node[1]["x"])
        y = int(node[1]["y"])
        draw_node(draw, x, y, node[1]["name"])

    draw.text((10, 10), "Time: %ds" % i, fill="black")
    draw_progress(draw, 10, img_size[1] - 10, i / max_time, img_size[0] - 20)

    return image


max_steps = max_time

for i in range(0, max_steps, args.step_size):

    image = draw_network(g, plan.connections_at_time(i))
    frames.append(image)


frame_one = frames[0]
frame_one.save(
    args.output,
    format="GIF",
    append_images=frames,
    save_all=True,
    duration=100,
    loop=0,
    optimize=True,
)
