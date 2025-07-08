from pons.node import Node
from jinja2.utils import pass_context
from platform import node


class ManagementInformationBase:
    def __init__(self):
        self.data = {}
        # Initialize with required DTN management information from yang model
        self.data["node"] = {
            "versions": [7],
            "endpoint_identifier": None,
            "neighbors": [],
            "store": {
                "maximum-size": 0,
                "current-size": 0,
                "maximum-bundles": 0,
                "bundles_number": 0,
            },
            "bundle-state-information": {  # from CCSDS Bundle Protocol V7 Orange Book
                "forward-pending-bundles": 0,
                "dispatch-pending-bundles": 0,
                "reassembly-pending-bundles": 0,
                "bundles-sourced": 0,
                "bulk-bundles-queued": 0,  # same as store.bundles_number
                "fragmentation-bundles-created": 0,
                "number-of-fragments-created": 0,
            },
            "bundle-processing-errors": {
                "failed_forwarding-bundles": 0,
                "abandoned_delivery-bundles": 0,
                "discarded_bundles": 0,
            },
            "registrations": [],
        }

    def sync(self, node: Node):
        self.data["node"]["registrations"].clear()
        node_number = node.id
        self.data["node"]["endpoint_identifier"] = node_number
        self.data["node"]["neighbors"] = [n.id for n in node.router.peers]
        self.data["store"]["maximum-size"] = node.router.capacity
        self.data["store"]["current-size"] = node.router.used
        for app in node.router.apps:
            service_number = app.service
            self.data["node"]["registrations"].append(f"{node_number}.{service_number}")

    def get(self, path):
        """Get the value at the specified path."""
        keys = path.split("/")
        data = self.data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return None
        return data

    def set(self, path, value):
        """Set the value at the specified path."""
        keys = path.split("/")
        data = self.data
        for key in keys[:-1]:
            if not isinstance(data, dict):
                # Cannot set item on non-dict, abort
                return
            if key not in data:
                data[key] = {}
            data = data[key]
        if not isinstance(data, dict):
            # Cannot set item on non-dict, abort
            return
        data[keys[-1]] = value
