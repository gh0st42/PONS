#!/usr/bin/env python3

import logging
import sys
import json
import os
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
try:
    import pons
except ImportError:
    sys.path.append(str(SCRIPT_DIR.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)


from pons.net.plans.parser import read_csv, read_json, read_ccp
from pons.net.plans import Contact, CommonContactPlan

logger = logging.getLogger(__name__)


def load_mapping_json(filename: str) -> dict[str, any]:
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


def main():
    mapping = load_mapping_json("scenario/simple_test/nodes.json")
    print("Node Mapping:", mapping)
    map: dict[str, int] = {nid: node["node_number"] for nid, node in mapping.items()}

    # Example usage of read_csv
    csv_contacts = read_csv("scenario/simple_test/contacts.csv", mapping=map)
    # logger.info(f"Contacts from CSV: {csv_contacts}")
    # print("Contacts from CSV:", csv_contacts)
    for c in csv_contacts:
        print(c)

    print("Number of Contacts from CSV:", len(csv_contacts))

    # Example usage of read_json
    json_contacts = read_json("scenario/simple_test/contacts.json", mapping=map)
    # logger.info(f"Contacts from JSON: {json_contacts}")
    # print("Contacts from JSON:", json_contacts)
    for c in json_contacts:
        print(c)
    print("Number of Contacts from JSON:", len(json_contacts))

    print("CSV == JSON", csv_contacts == json_contacts)

    # Example usage of read_corecontactplan
    ccp_contacts = read_ccp("scenario/simple_test/contacts.ccp", mapping=map)
    # print("Contacts from CCP:", ccp_contacts)
    for c in ccp_contacts:
        print(c)
    print("Number of Contacts from CCP:", len(ccp_contacts))

    print("CSV == CCP", csv_contacts == ccp_contacts)
    print("JSON == CCP", json_contacts == ccp_contacts)


if __name__ == "__main__":
    main()
