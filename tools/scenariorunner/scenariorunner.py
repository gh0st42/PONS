#!/usr/bin/env python3

import json
import networkx as nx
from pprint import pp
import sys
from typing import List, Dict, Any
import pathlib
import argparse
import logging
import os
import shutil

try:
    from . import scenariohelper
except ImportError:
    import scenariohelper

logger = logging.getLogger("__name__")


SCRIPT_DIR = pathlib.Path(__file__).parent.parent.resolve()
try:
    import pons
except ImportError:
    sys.path.append(str(SCRIPT_DIR.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)


def visualize_events(event_log: str, args: argparse.Namespace = None):
    """
    Visualize the events in the event log.
    This function is a placeholder and does not implement any visualization.
    """

    if not event_log:
        logger.warning(
            "No log file specified. Set the LOG_FILE environment variable to visualize events."
        )
        return

    frame_delay = args.visualization_frame_delay
    step_size = args.visualization_step_size

    ponsanimargs = f"-e {event_log} -H -x store -x bundles_rxtx -x app_rxtx -s {step_size} -d {frame_delay}"

    if not args.visualize:
        logger.info("No visualization file specified. Skipping visualization.")
        logger.info("To manually visualize, run:")
        logger.info(f"ponsanim.py {ponsanimargs} -o out.mp4")
        return

    ponsanimargs += f" -o {args.visualize}"

    logger.info("Visualizing the network graph...")

    # check if ponsanim.py is in PATH by calling which ponsanim.py

    ponsanim_path = shutil.which("ponsanim.py")
    if not ponsanim_path:
        logger.error("ponsanim.py not found in PATH. Please install ponsanim.")
        sys.exit(1)

    logger.info(f"Visualizing events from {event_log}...")

    if args.visualize.endswith(".gif"):
        logger.warning(
            "Visualizing to GIF is slow and memory intensive. Please consider using mp4 format for visualization."
        )

    ret = os.system(f"ponsanim.py {ponsanimargs}")
    if ret != 0:
        logger.error(
            "Error running ponsanim.py. Please check the command and try again."
        )
        sys.exit(1)
    if args.visualize.endswith(".mp4"):
        os.system(
            f"ffmpeg -y -i {args.visualize} -c:v libx264 -pix_fmt yuv420p -y {args.visualize}.compressed.mp4"
        )
    logger.info(f"Visualization saved to {args.visualize}.")


def run_scenario(
    g: nx.Graph,
    contacts: List[Dict[str, Any]],
    flows: List[Dict[str, Any]],
    args: argparse.Namespace,
):
    logger.info(
        f"Running scenario with {len(g.nodes)} nodes, {len(g.edges)} links and {len(contacts)} contacts..."
    )
    core_contacts = pons.net.CoreContactPlan(contacts=contacts, symmetric=False)
    plan = pons.net.NetworkPlan(g, contacts=core_contacts)
    router_class = getattr(pons.routing, args.router, None)
    # check if router_class constructor accepts a graph parameter
    if "graph" in router_class.__init__.__code__.co_varnames:
        # if the router class has a graph parameter, pass the graph to the constructor
        logger.info(f"Using {args.router} with graph parameter.")
        router = router_class(graph=g)
    else:
        router = router_class()
    # router = pons.routing.EpidemicRouter()
    logger.info(f"Generating {len(g.nodes)} {args.router} nodes...")
    nodes = plan.generate_nodes(router=router)
    config = {
        "movement_logger": False,
        "peers_logger": False,
    }

    max_runtime = args.sim_time if args.sim_time else contacts[-1].timespan[1]
    logger.info(f"Max runtime set to {max_runtime} seconds.")

    msg_gens = []

    if not args.use_app:
        for f in flows:
            if f["src_scheme"] != "ipn" or f["dst_scheme"] != "ipn":
                logger.error(
                    f"Flow {f['id']} has unsupported src or dst scheme: {f['src_scheme']}, {f['dst_scheme']}"
                )
                sys.exit(1)
            # convert flows to message generators

            msg_gen = {
                "type": "single",
                "interval": f["rate"],
                "src": f["src_id"],
                "src_service": f["src_service"],
                "dst": f["dst_id"],
                "dst_service": f["dst_service"],
                "size": f["size"],
                "id": f["type"] + "-",
                "ttl": max_runtime,  # use max_runtime as ttl
                "start_time": f.get("start_time", 0),  # default to 0 if not specified
                "end_time": f.get("end_time", -1),  # default to -1 if not specified
            }
            msg_gens.append(msg_gen)

    # print("Message Generators:")
    # pp(msg_gens)
    netsim = pons.NetSim(max_runtime, nodes, config=config, msggens=msg_gens)

    if args.use_app:
        for f in flows:
            sender_app = pons.apps.SenderApp(
                service=f["src_service"],
                dst=f["dst_id"],
                dst_service=f["dst_service"],
                interval=f["rate"],
                ttl=max_runtime,  # use max_runtime as ttl
                size=f["size"],
                msg_prefix=f["type"],
                active_time=(f.get("start_time", 0), f.get("end_time", -1)),
            )
            netsim.install_app(
                f["src_id"],
                sender_app,
            )
            sink_app = pons.apps.SinkApp(
                service=f["dst_service"],
            )
            netsim.install_app(
                f["dst_id"],
                sink_app,
            )

    logger.info("Setting up the simulation...")
    netsim.setup()

    for i, n in netsim.nodes.items():
        logger.info(
            f"{i}: Node {n.node_id} ({i}) - Router: {n.router.__class__.__name__}, "
            f"Position: {n.x} {n.y}, Services: {n.router.apps}"
        )

    logger.info("Running the simulation...")
    netsim.run()

    logger.info("Simulation finished.")
    print(json.dumps(netsim.net_stats, indent=4))
    print(json.dumps(netsim.routing_stats, indent=4))

    log_file = os.getenv("LOG_FILE")
    visualize_events(log_file, args)


def main():

    valid_routers = []
    # get a list of all subclasses of pons.routing.Router
    for name, obj in pons.routing.__dict__.items():
        if (
            isinstance(obj, type)
            and issubclass(obj, pons.routing.Router)
            and obj is not pons.routing.Router
        ):
            valid_routers.append(name)

    parser = argparse.ArgumentParser(description="Run a CSV/JSON scenario.")
    parser.add_argument(
        "--contacts",
        "-c",
        type=str,
        required=True,
        help="CSV file with contacts",
    )
    parser.add_argument(
        "--nodes", "-n", type=str, help="Node mapping JSON file", required=True
    )
    parser.add_argument(
        "--flows",
        "-f",
        type=str,
        help="JSON file with application traffic flows",
    )
    parser.add_argument(
        "--router",
        "-r",
        type=str,
        choices=valid_routers,
        default="EpidemicRouter",
        help="Router to use for the scenario",
    )
    parser.add_argument(
        "--sim-time",
        "-t",
        type=int,
        help="Simulation time in seconds (default: taken from last entry in contacts file)",
    )
    parser.add_argument(
        "--visualize",
        "-V",
        type=str,
        help="Visualize the network graph after the simulation and store as mp4 video (requires ponsanim.py and ffmpeg in PATH)",
    )
    parser.add_argument(
        "--visualization-frame-delay",
        "-D",
        type=int,
        default=100,
        help="Frame delay for the visualization in milliseconds (default: 100)",
    )
    parser.add_argument(
        "--visualization-step-size",
        "-S",
        type=int,
        default=100,
        help="Step size for the visualization (default: 100)",
    )
    parser.add_argument(
        "--use-app",
        "-A",
        action="store_true",
        help="Use application layer traffic, otherwise just bundle flow on router layer (default: False)",
    )
    args = parser.parse_args()

    node_mapping = scenariohelper.load_mapping_json(args.nodes)
    g = scenariohelper.get_graph_from_csv(args.contacts, node_mapping)
    # rename nodes to integers from their node_id
    mapping = {}
    for k, v in node_mapping.items():
        mapping[k] = v["node_number"]
    g = nx.relabel_nodes(g, mapping)

    contacts = scenariohelper.get_contacts_from_csv(args.contacts, node_mapping)
    flows = scenariohelper.load_application_traffic(args.flows, node_mapping)
    run_scenario(g, contacts, flows, args)


if __name__ == "__main__":
    main()
