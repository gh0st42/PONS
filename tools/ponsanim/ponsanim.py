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


def draw_node(img, x, y, name="", store_usage=None, app_rx=False, app_tx=False):
    if name:
        img.text((x + 6, y + 6), name, fill="black")
    if store_usage is not None:
        # img.text((x + 6, y + 20), "Store: %d%%" % store_usage, fill="black")
        # draw up to four blocks representing the store usage
        if store_usage > 0:
            num_blocks = store_usage // 25

            num_blocks += 1
            for i in range(num_blocks):
                color = "blue"
                if store_usage > 95:
                    color = "red"
                if i > 4:
                    break
                # img.rectangle(
                #     [x + 6 + i * 5 + i * 2, y + 20, x + 10 + i * 5 + i * 2, y + 24],
                #     fill=color,
                # )
                img.rectangle(
                    [x + 14, y - i * 5 - i * 2, x + 18, y + 4 - i * 5 - i * 2],
                    fill=color,
                )

    img.circle((x, y), 8, fill="blue")
    if app_rx:
        img.circle((x, y), 14, outline="green", width=2)
    if app_tx:
        img.circle((x, y), 12, outline="blue", width=2)


def draw_network(
    g, connections=[], i=0, active_links=[], app_rx=[], app_tx=[], human_readable=False
):
    global max_x, max_y, img_size, max_time
    image = Image.new("RGB", img_size, "white")
    draw = ImageDraw.Draw(image)

    # draw the links
    for edge in connections:
        color = "black"
        w = 1
        link = tuple(sorted([edge[0], edge[1]]))
        if link in active_links:
            color = "green"
            w = 4
        x1 = int(g.nodes[edge[0]]["x"])
        y1 = int(g.nodes[edge[0]]["y"])
        x2 = int(g.nodes[edge[1]]["x"])
        y2 = int(g.nodes[edge[1]]["y"])
        draw.line((x1, y1, x2, y2), fill=color, width=w)

    # draw the nodes
    for node in g.nodes.data():
        x = int(node[1]["x"])
        y = int(node[1]["y"])
        store_usage = None
        if "store" in node[1]:
            store_usage = node[1]["store"]
        else:
            # print("No store usage information for node %d" % node[0])
            pass
        draw_node(
            draw,
            x,
            y,
            node[1]["name"],
            store_usage=store_usage,
            app_tx=node[0] in app_tx,
            app_rx=node[0] in app_rx,
        )
    time_str = "Time: %ds" % i
    if human_readable:
        days = i // (24 * 3600)
        hours = (i % (24 * 3600)) // 3600
        minutes = (i % 3600) // 60
        seconds = i % 60
        time_str = "Time: %sd %sh %sm %ss" % (
            days,
            str(hours).rjust(2, "0"),
            str(minutes).rjust(2, "0"),
            str(seconds).rjust(2, "0"),
        )

    draw.text((10, 10), time_str, fill="black")
    draw_progress(draw, 10, image.height - 10, i / max_time, image.width - 20)

    return image


import math

max_x = 0
max_y = 0
extra_x = 50
extra_y = 50
min_x = math.inf
min_y = math.inf
max_time = 0
img_size = (0, 0)


def main():
    global max_x, max_y, max_time, img_size, min_x, min_y, extra_x, extra_y
    parser = argparse.ArgumentParser(description="Animate a network replay / event log")
    parser.add_argument(
        "-o", "--output", type=str, help="The output image file", required=True
    )
    parser.add_argument(
        "-s", "--step-size", type=int, help="Step size in seconds", default=100
    )
    parser.add_argument(
        "-d", "--delay", type=int, help="Delay between frames in ms", default=100
    )
    parser.add_argument(
        "-H",
        "--human-readable-timestamp",
        help="Convert timestamp from seconds to days, hours, minutes and seconds",
        action="store_true",
    )
    parser.add_argument("-g", "--graph", type=str, help="Input graphml file")
    parser.add_argument("-c", "--contacts", type=str, help="The network contacts file")
    parser.add_argument(
        "-t",
        "--time-limit",
        type=int,
        help="The maximum simulation time to animate, default is taken from the event log / contact plan",
    )
    parser.add_argument("-e", "--event-log", type=str, help="The event log file")
    parser.add_argument(
        "-x",
        "--extra-information",
        action="append",
        help="Extra information to plot, e.g., store usage or bundle transmissions",
        choices=["store", "bundles_rxtx", "app_rxtx"],
    )

    args = parser.parse_args()
    # calculate fps from delay in ms per frame
    fps = 1000 / args.delay
    modeContactGraph = False
    if args.graph is not None and args.contacts is not None:
        modeContactGraph = True

    if not modeContactGraph and args.event_log is None:
        print(
            "You need to specify either a graph and contacts file or an event log file"
        )
        sys.exit(1)

    frames = []

    node_map = {}
    output_mp4 = False
    if args.output.endswith(".mp4"):
        output_mp4 = True
        try:
            import cv2
            import numpy as np
        except ImportError:
            print("You need to have OpenCV (opencv-python) installed to save to MP4")

    if modeContactGraph:
        # print(args.graph)
        g = nx.read_graphml(args.graph, node_type=int)

        for node in g.nodes.data():
            print(node)
            x = int(node[1]["x"])
            y = int(node[1]["y"])
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            node_map[node[1]["name"]] = node[0]
        cplan = CoreContactPlan.from_file(args.contacts, node_map)
        max_time = cplan.get_max_time()

    else:
        filter_in = ["CONFIG", "LINK", "MOVE"]
        if args.extra_information is None:
            args.extra_information = []
        if "store" in args.extra_information:
            filter_in.append("STORE")
        if "bundles_rxtx" in args.extra_information:
            filter_in.append("ROUTER")
        if "app_rxtx" in args.extra_information:
            filter_in.append("APP")

        events, max_time = load_event_log(args.event_log, filter_in=filter_in)
        g = nx.Graph()
        contacts = []
        for ts, e_list in events.items():
            # print(ts, e_list)
            for ts, cat, event in e_list:
                if cat == "CONFIG":
                    x = int(event["x"])
                    y = int(event["y"])
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
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

        for n in g.nodes.keys():
            if "store" in args.extra_information:
                g.nodes[n]["store"] = 0

        if len(contacts) > 0:
            cplan = CoreContactPlan(contacts=contacts)
        else:
            cplan = None

    if args.time_limit is not None:
        max_time = args.time_limit
    extra_x = max(extra_x, min_x)
    extra_y = max(extra_y, min_y)
    img_size = (max_x + extra_x, max_y + extra_y)
    print(img_size)
    print(max_time)
    plan = NetworkPlan(g, cplan)

    max_steps = max_time

    for i in progressBar(
        range(0, max_steps + 1, args.step_size),
        prefix="Progress:",
        suffix="Complete",
        length=50,
    ):
        active_links = set()
        apps_rx = set()
        apps_tx = set()
        if not modeContactGraph:
            for ts, cat, event in get_events_in_range(events, i - args.step_size, i):
                if cat == "MOVE":
                    if event["event"] == "SET":
                        g.nodes[event["id"]]["x"] = int(event["x"])
                        g.nodes[event["id"]]["y"] = int(event["y"])
                elif cat == "STORE" and "store" in args.extra_information:
                    if event["capacity"] > 0:
                        usage = int(event["used"] / event["capacity"] * 100)
                        g.nodes[event["id"]]["store"] = usage
                        # print("Store usage: %d%% on node %d" % (usage, event["id"]))
                    else:
                        print(
                            "Capacity is 0 - deactivating store visualization for node %d"
                            % event["id"]
                        )
                        g.nodes[event["id"]]["store"] = None
                elif cat == "ROUTER" and "bundles_rxtx" in args.extra_information:

                    if event["event"] == "TX" or event["event"] == "RX":
                        link = sorted([int(event["src"]), int(event["dst"])])
                        active_links.add(tuple(link))
                elif cat == "APP" and "app_rxtx" in args.extra_information:
                    if event["event"] == "TX":
                        apps_tx.add(int(event["src"]))
                    if event["event"] == "RX":
                        apps_rx.add(int(event["id"]))
        image = draw_network(
            g,
            plan.connections_at_time(i),
            i,
            active_links=list(active_links),
            app_rx=list(apps_rx),
            app_tx=list(apps_tx),
            human_readable=args.human_readable_timestamp,
        )
        if output_mp4:
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        frames.append(image)

    if output_mp4:
        print("Saving MP4...")
        out = cv2.VideoWriter(
            args.output,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            img_size,
        )
        for frame in frames:
            out.write(frame)
        out.release()
        print()
        print(
            f"{args.output} is an uncompressed MP4. You might want to use ffmpeg to compress it."
        )
        print(
            "You can use the following command to compress the MP4 file using ffmpeg:"
        )
        print(
            f"ffmpeg -i {args.output} -c:v libx264 -pix_fmt yuv420p {args.output}.compressed.mp4"
        )
    else:
        print("Saving GIF...")
        frame_one = frames[0]
        frame_one.save(
            args.output,
            format="GIF",
            append_images=frames,
            save_all=True,
            duration=args.delay,
            loop=0,
            optimize=False,
        )
        print()
        print(f"Saved unoptimized GIF to {args.output}. You might want to optimize it.")
        print("You can use the following command to optimize the GIF using gifsicle:")
        print(f"gifsicle -O3 --colors 16 {args.output} -o {args.output}.optimized.gif")
    print("Done.")


if __name__ == "__main__":
    main()
