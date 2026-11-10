import argparse
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tools" / "scenariorunner"))

import scenariohelper
import scenariorunner

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"
CCSDS = EXAMPLES / "scenarios" / "ccsds"
LUNAR = CCSDS / "lunar-communication" / "v1.0"
SIMPLE_TEST = EXAMPLES / "scenario" / "simple_test"


class ScenarioLoaderTests(unittest.TestCase):
    """Tests for loading CCSDS DTN reference scenario files."""

    def test_load_mapping_json(self):
        mapping = scenariohelper.load_mapping_json(str(LUNAR / "nodes.json"))
        self.assertEqual(len(mapping), 14)
        self.assertEqual(mapping["lbcc"]["name"], "Lunar Base Control Centre")
        self.assertEqual(mapping["lbcc"]["node_id"], "ipn:10.0")
        self.assertEqual(mapping["lbcc"]["node_number"], 10)
        self.assertEqual(mapping["lgw"]["node_number"], 220)

    def test_load_mapping_json_requires_unique_ipn_ids(self):
        import json
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {"node_label": "a", "node_name": "A", "node_id": "ipn:1.0"},
                    {"node_label": "b", "node_name": "B", "node_id": "ipn:1.0"},
                ],
                f,
            )
            name = f.name
        with self.assertRaises(SystemExit):
            scenariohelper.load_mapping_json(name)
        import os

        os.unlink(name)

    def test_load_application_traffic(self):
        mapping = scenariohelper.load_mapping_json(str(LUNAR / "nodes.json"))
        flows = scenariohelper.load_application_traffic(
            str(LUNAR / "traffic.json"), mapping
        )
        self.assertEqual(len(flows), 15)
        flow = flows[0]
        self.assertEqual(flow["src_id"], 11)
        self.assertEqual(flow["src_service"], 1)
        self.assertEqual(flow["dst_id"], 10)
        self.assertEqual(flow["dst_service"], 1)
        self.assertEqual(flow["size"], 64000)
        self.assertEqual(flow["rate"], 60)
        self.assertEqual(flow["ttl"], 2592000)
        self.assertTrue(flow["info"])

    def test_application_traffic_target_must_be_known(self):
        mapping = scenariohelper.load_mapping_json(str(LUNAR / "nodes.json"))
        with self.assertRaises(SystemExit):
            scenariohelper.load_application_traffic(
                str(SIMPLE_TEST.parent / "application_data.json"), mapping
            )

    def test_load_application_traffic_missing_optional_ttl(self):
        mapping = scenariohelper.load_mapping_json(
            str(SIMPLE_TEST / "nodes.json")
        )
        flows = scenariohelper.load_application_traffic(
            str(SIMPLE_TEST / "flows.json"), mapping
        )
        self.assertEqual(flows[0]["ttl"], -1)

    def test_load_scenario_dir(self):
        files = scenariohelper.load_scenario_dir(str(LUNAR))
        self.assertEqual(files["nodes"], str(LUNAR / "nodes.json"))
        self.assertEqual(
            files["planned_contacts"], str(LUNAR / "planned_contacts.csv")
        )
        self.assertEqual(
            files["actual_contacts"], str(LUNAR / "actual_contacts.csv")
        )
        self.assertEqual(files["traffic"], str(LUNAR / "traffic.json"))

    def test_load_scenario_dir_requires_core_files(self):
        with self.assertRaises(SystemExit):
            scenariohelper.load_scenario_dir(str(CCSDS))

    def test_get_graph_from_contacts(self):
        mapping = scenariohelper.load_mapping_json(str(LUNAR / "nodes.json"))
        contacts = scenariorunner.read_contacts_file(
            str(LUNAR / "planned_contacts.csv"), _ipn_mapping(mapping)
        )
        self.assertTrue(len(contacts) > 100)
        g = scenariohelper.get_graph_from_contacts(contacts, mapping)
        self.assertEqual(len(g.nodes), 14)

    def test_read_contacts_file_rejects_unknown_format(self):
        with self.assertRaises(SystemExit):
            scenariorunner.read_contacts_file("contacts.txt", {})


class ScenarioRunTests(unittest.TestCase):
    """Tests for running CCSDS DTN reference scenarios with the scenariorunner."""

    def _args(self, router, sim_time):
        return argparse.Namespace(
            router=router,
            sim_time=sim_time,
            use_app=False,
            visualize=None,
            visualization_frame_delay=100,
            visualization_step_size=100,
        )

    def _run_simple_test(self, actual_contacts=None):
        mapping_obj = scenariohelper.load_mapping_json(
            str(SIMPLE_TEST / "nodes.json")
        )
        mapping = _ipn_mapping(mapping_obj)
        planned = scenariorunner.read_contacts_file(
            str(SIMPLE_TEST / "contacts.csv"), mapping
        )
        actual = actual_contacts if actual_contacts is not None else planned
        g = scenariohelper.get_graph_from_contacts(planned, mapping_obj)
        import networkx as nx

        g = nx.relabel_nodes(g, mapping)
        flows = scenariohelper.load_application_traffic(
            str(SIMPLE_TEST / "flows.json"), mapping_obj
        )
        self.assertTrue(len(flows) > 0)
        # capture the stats printed by run_scenario
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            scenariorunner.run_scenario(g, planned, actual, flows, self._args("EpidemicRouter", 240))
        return buf.getvalue()

    def test_run_simple_test_scenario(self):
        out = self._run_simple_test()
        self.assertIn('"created"', out)
        # the flow runs on a static n1-n2 link and intermittent n2-n3
        # contacts, so some bundles must be delivered within 240 seconds
        self.assertIn('"delivered"', out)
        self.assertNotIn('"delivered": 0', out)

    def test_run_with_reduced_actual_contacts(self):
        # same planned contacts, but the first contact window is dropped
        # from the actual contacts, so all traffic must wait for the later
        # windows that only open after the first bundles expired
        mapping_obj = scenariohelper.load_mapping_json(
            str(SIMPLE_TEST / "nodes.json")
        )
        mapping = _ipn_mapping(mapping_obj)
        planned = scenariorunner.read_contacts_file(
            str(SIMPLE_TEST / "contacts.csv"), mapping
        )
        actual = [
            c
            for c in planned
            if not (c.fixed and c.nodes[0] == 1 and c.nodes[1] == 2)
        ]
        self.assertTrue(len(actual) < len(planned))
        out = self._run_simple_test(actual_contacts=actual)
        self.assertIn('"created"', out)


def _ipn_mapping(mapping_obj):
    return {k: v["node_number"] for k, v in mapping_obj.items()}


if __name__ == "__main__":
    unittest.main()
