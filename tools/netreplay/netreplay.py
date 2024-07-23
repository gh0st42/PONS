#!/usr/bin/env python3

import sys
import networkx as nx
from PIL import Image, ImageDraw
import argparse

try:
    import pons
except ImportError:
    sys.path.append("../../")

from pons.net.contactplan import CoreContactPlan, CoreContact
from pons.net.netplan import NetworkPlan
from pons.event_log import get_events_in_range, load_event_log


def progressBar(
    iterable, prefix="", suffix="", decimals=1, length=100, fill="█", printEnd="\r"
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(
            100 * (iteration / float(total))
        )
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + "-" * (length - filledLength)
        print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)

    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


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


parser = argparse.ArgumentParser(description="Visualize a network replay")
parser.add_argument(
    "-o", "--output", type=str, help="The output image file", required=True
)
parser.add_argument(
    "-s", "--step-size", type=int, help="Step size in seconds", default=100
)
parser.add_argument(
    "-d", "--delay", type=int, help="Delay between frames in ms", default=100
)
parser.add_argument("-g", "--graph", type=str, help="Input graphml file")
parser.add_argument("-c", "--contacts", type=str, help="The network contacts file")
parser.add_argument("-e", "--event-log", type=str, help="The event log file")

args = parser.parse_args()
modeContactGraph = False
if args.graph is not None and args.contacts is not None:
    modeContactGraph = True

if not modeContactGraph and args.event_log is None:
    print("You need to specify either a graph and contacts file or an event log file")
    sys.exit(1)

frames = []
max_x = 0
max_y = 0
node_map = {}
max_time = 0

if modeContactGraph:
    # print(args.graph)
    g = nx.read_graphml(args.graph, node_type=int)

    for node in g.nodes.data():
        print(node)
        x = int(node[1]["x"])
        y = int(node[1]["y"])
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        node_map[node[1]["name"]] = node[0]
    cplan = CoreContactPlan.from_file(args.contacts, node_map)
    max_time = cplan.get_max_time()

else:
    events = load_event_log(args.event_log, filter_in=["CONFIG", "LINK", "MOVE"])
    g = nx.Graph()
    contacts = []
    for ts, e_list in events.items():
        # print(ts, e_list)
        for ts, cat, event in e_list:
            if cat == "CONFIG":
                x = int(event["x"])
                y = int(event["y"])
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                g.add_node(event["id"], x=x, y=y, name=event["name"])
            elif cat == "LINK":
                if event["event"] == "UP":
                    contact = CoreContact((ts, -1), event["nodes"], 0, 0, 0, 0)
                    contacts.append(contact)
                if event["event"] == "DOWN":
                    for c in contacts:
                        if c.nodes == event["nodes"] and c.timespan[1] == -1:
                            timespan = (c.timespan[0], ts)
                            contacts.remove(c)
                            c = CoreContact(timespan, event["nodes"], 0, 0, 0, 0)
                            contacts.append(c)
                if event["event"] == "SET":
                    g.add_edge(event["node1"], event["node2"])
    if len(contacts) > 0:
        cplan = CoreContactPlan(contacts=contacts)
    else:
        cplan = None
    max_time = sorted(events.keys())[-1]

print("Max time: %d" % max_time)
img_size = (max_x + 50, max_y + 50)
print(max_x + 50, max_y + 50)

plan = NetworkPlan(g, cplan)

max_steps = max_time

for i in progressBar(
    range(0, max_steps + 1, args.step_size),
    prefix="Progress:",
    suffix="Complete",
    length=50,
):
    if not modeContactGraph:
        for ts, cat, event in get_events_in_range(events, i - args.step_size, i):
            if cat == "MOVE":
                if event["event"] == "SET":
                    g.nodes[event["id"]]["x"] = int(event["x"])
                    g.nodes[event["id"]]["y"] = int(event["y"])

    image = draw_network(g, plan.connections_at_time(i))
    frames.append(image)

    # sys.exit(0)

print("Saving GIF...")
frame_one = frames[0]
frame_one.save(
    args.output,
    format="GIF",
    append_images=frames,
    save_all=True,
    duration=args.delay,
    loop=0,
    optimize=True,
)
print("Done.")
