#!/usr/bin/env python3

import csv
import json
import networkx as nx
from pprint import pp
import sys
from typing import List, Dict, Any
import pathlib
import logging

logger = logging.getLogger(__name__)

SCRIPT_DIR = pathlib.Path(__file__).parent.parent.resolve()
try:
    import pons
except ImportError:
    sys.path.append(str(SCRIPT_DIR.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

from pons.net.plans import bandwidth_parser, Contact


def load_mapping_json(filename: str) -> Dict[str, Any]:
    logger.info(f"Loading node mapping from {filename}")
    with open(filename, "r") as f:
        data = json.load(f)
    mapping = {}
    used_ids = set()
    for node in data:
        node_number = 1
        if node["node_id"].startswith("ipn:"):
            node_number = int(node["node_id"].split(":")[1].split(".")[0])
            if node_number in used_ids:
                logger.error(
                    f"Duplicate node_id {node_number} found in {filename}. "
                    "Please check the mapping file."
                )
                sys.exit(1)
            used_ids.add(node_number)
        else:
            while node_number in used_ids:
                node_number += 1
            used_ids.add(node_number)

        mapping[node["id"]] = {
            "name": node["name"],
            "node_id": node["node_id"],
            "node_number": node_number,
        }
    return mapping


def get_node_details_from_mapping(
    mapping: dict, node_id: str | int
) -> tuple[int, str, str]:
    if isinstance(node_id, str):
        if node_id in mapping:
            return mapping[node_id]["node_number"], node_id, mapping[node_id]["name"]
        else:
            raise ValueError(f"Node {node_id} not found in mapping {mapping.keys()}")
    else:
        for c in mapping:
            if mapping[c]["node_number"] == node_id:
                return mapping[c]["node_number"], c, mapping[c]["name"]
        # create new node entry if not found
        new_node_id = f"n{node_id}"
        mapping[new_node_id] = {
            "node_number": node_id,
            "name": new_node_id,
            "node_id": f"ipn:{node_id}.0",
        }
        return node_id, new_node_id, new_node_id


def get_graph_from_contacts(contacts: list[Contact], mapping: dict) -> nx.MultiDiGraph:
    logger.info(f"Loading network graph from contacts")
    G = nx.MultiDiGraph()
    for c in contacts:
        n1_id, n1_short, n1_name = get_node_details_from_mapping(mapping, c.nodes[0])
        n2_id, n2_short, n2_name = get_node_details_from_mapping(mapping, c.nodes[1])
        ts_start = c.timespan[0]
        ts_end = c.timespan[1]
        bw = c.bw
        delay = c.delay
        label = c.label if hasattr(c, "label") else ""

        G.add_node(
            n1_short,
            name=n1_name,
            type="Host",
            node_id=n1_id,
        )
        G.add_node(
            n2_short,
            name=n2_name,
            type="Host",
            node_id=n2_id,
        )

        dynamic_link = True
        if ts_start == 0 and ts_end == -1:
            dynamic_link = False

        if not G.has_edge(n1_id, n2_id, key=label):
            logger.debug("Adding edge: %s %s %s" % (n1_id, n2_id, label))
            G.add_edge(
                n1_short,
                n2_short,
                key=label,
                dynamic_link=dynamic_link,
                bw=bw,
                delay=delay,
                loss=0,
                jitter=0,
                label=label,
            )
    MARGIN = 50
    SCALE = 1000
    # if sys.implementation.name == "pypy":
    #     logger.warning(
    #         "Using PyPy, setting node positions in a grid layout. "
    #         "This may not be optimal for large graphs."
    #     )
    #     cnt = 0
    #     # arrange all nodes with X and Y coordinates in a grid with 50 units spacing
    #     for node in G.nodes(data=True):
    #         node_id = node[0]
    #         G.nodes[node_id]["x"] = MARGIN + (cnt % 10) * 50
    #         G.nodes[node_id]["y"] = MARGIN + (cnt // 10) * 50
    #         cnt += 1
    # else:
    pos = nx.spring_layout(G, seed=42)  # use spring layout for initial positions
    min_x = min(x for x, y in pos.values()) * SCALE
    min_y = min(y for x, y in pos.values()) * SCALE
    for node, (x, y) in pos.items():
        G.nodes[node]["x"] = MARGIN + abs(min_x) + x * SCALE  # scale to 1000 units
        G.nodes[node]["y"] = MARGIN + abs(min_y) + y * SCALE  # scale to 1000 units

    logger.debug("Loaded node data: %s", G.nodes(data=True))
    return G


def get_contacts_from_csv(
    csvfile: str | None, json_mapping=None
) -> List[Dict[str, Any]]:
    logger.info(f"Loading contacts from {csvfile}")
    contacts = []
    if not csvfile:
        return contacts

    with open(csvfile, "r") as f:
        f.readline()  # skip header
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 6 or len(row) == 7:
                if row[0].startswith("#"):
                    continue
                node1 = row[0]
                if json_mapping is not None and node1 in json_mapping:
                    node1 = json_mapping[node1]["node_number"]
                node2 = row[1]
                if json_mapping is not None and node2 in json_mapping:
                    node2 = json_mapping[node2]["node_number"]
                ts_start = float(row[2])
                ts_end = float(row[3])
                if ts_end == -1:
                    # skipping fixed links
                    continue
                bw = bandwidth_parser(row[4])

                delay = float(row[5])
                label = row[6] if len(row) == 7 else ""

                contact = pons.net.Contact(
                    timespan=(ts_start, ts_end),
                    nodes=(node1, node2),
                    bw=bw,
                    delay=delay,
                    jitter=0,
                    loss=0,
                )

                contacts.append(contact)
    return contacts


def extract_from_ipn(node_id: str) -> tuple[int, int]:
    if node_id.startswith("ipn:"):
        node_id = node_id.split(":")[1]
        if "." in node_id:
            node_id, node_service = node_id.split(".")
            return (int(node_id), int(node_service))
        return int(node_id), 0
    else:
        raise ValueError(f"Invalid node_id format: {node_id}")


def load_application_traffic(filename: str, json_mapping: Dict) -> List[Dict[str, Any]]:
    logger.info(f"Loading application traffic flows from {filename}")
    traffic = []
    valid_node_ids = []
    for node in json_mapping:
        node_id = json_mapping[node]["node_number"]
        valid_node_ids.append(node_id)

    json_app_data = json.load(open(filename, "r"))
    for flow in json_app_data:
        src = flow["src"]
        if not src.startswith("ipn:"):
            logger.error(f"src {src} does not start with ipn:")
            continue
        src_id, src_service = extract_from_ipn(flow["src"])
        if not src_id in valid_node_ids:
            logger.error(
                f"src {src} not found in scenario nodes while loading application traffic flows"
            )
            sys.exit(1)

        dst = flow["dst"]
        if not dst.startswith("ipn:"):
            logger.error(f"dst {dst} does not start with ipn:")
            continue
        dst_id, dst_service = extract_from_ipn(flow["dst"])
        if not dst_id in valid_node_ids:
            logger.error(
                f"dst {dst} not found in scenario nodes while loading application traffic flows"
            )
            sys.exit(1)

        interval = (flow["start_time"], flow["end_time"])

        flow_type = flow.get("type", "MSG")
        if not "type" in flow.keys():
            logger.warning(
                f"Flow {flow} does not have a 'type'. Defaulting to 'MSG'.",
            )
            # try to get a type from the info field
            if "info" in flow and ":" in flow["info"]:
                logger.debug(
                    f"Flow {flow} does not have a type. Trying to extract from info field: {flow['info']}",
                )
                flow_type_extracted = flow["info"].split(":")[0]
                # extract any all uppercase words from the flow_type_extracted string
                flow_type_extracted = "_".join(
                    [word for word in flow_type_extracted.split() if word.isupper()]
                )
                if len(flow_type_extracted) > 0:
                    flow_type = flow_type_extracted
                    logger.info(
                        f"Extracted flow type {flow_type} from info field: {flow['info']}"
                    )
                else:
                    logger.warning(
                        f"Could not extract flow type from info field: {flow['info']}. Defaulting to 'MSG'."
                    )
                    flow_type = "MSG"

        traffic.append(
            {
                "src_scheme": "ipn",
                "src_id": src_id,
                "src_service": src_service,
                "dst_scheme": "ipn",
                "dst_id": dst_id,
                "dst_service": dst_service,
                "interval": interval,
                "type": flow_type,
                "size": flow["bundle_size"],
                "rate": flow["generation_rate_in_s"],
                "info": flow["info"],
                "start_time": flow.get("start_time", 0),
                "end_time": flow.get("end_time", -1),
            }
        )
    return traffic
