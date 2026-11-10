import argparse
import io
import pathlib
import random
import sys
import time
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tools" / "scenariorunner"))

import networkx as nx

import scenariohelper
import scenariorunner

CCSDS = (
    pathlib.Path(__file__).parent.parent / "examples" / "scenarios" / "ccsds"
)
SIMPLE_TEST = (
    pathlib.Path(__file__).parent.parent / "examples" / "scenario" / "simple_test"
)
SMOKE_SIM_TIME = 900

# the scenarios assert only coarse, stable properties; exact delivery counts
# depend on the router and the contact windows and would make the tests
# brittle
EXPECTED_NODES = {
    "lunar-communication": 14,
    "mars-communication": 12,
    "low-earth-orbit": 5,
}
EXPECTED_FLOWS = {
    "lunar-communication": 15,
    "mars-communication": 12,
    "low-earth-orbit": 3,
}


def _args(router, sim_time):
    return argparse.Namespace(
        router=router,
        sim_time=sim_time,
        use_app=False,
        visualize=None,
        visualization_frame_delay=100,
        visualization_step_size=100,
    )


def _load_scenario(scenario):
    files = scenariohelper.load_scenario_dir(str(CCSDS / scenario / "v1.0"))
    mapping_obj = scenariohelper.load_mapping_json(files["nodes"])
    mapping = {k: v["node_number"] for k, v in mapping_obj.items()}
    planned = scenariorunner.read_contacts_file(files["planned_contacts"], mapping)
    actual = scenariorunner.read_contacts_file(files["actual_contacts"], mapping)
    flows = scenariohelper.load_application_traffic(files["traffic"], mapping_obj)
    g = scenariohelper.get_graph_from_contacts(planned, mapping_obj)
    g = nx.relabel_nodes(g, mapping)
    return g, planned, actual, flows


def _run(g, planned, actual, flows, router="StaticRouter", sim_time=None):
    buf = io.StringIO()
    with redirect_stdout(buf):
        netsim = scenariorunner.run_scenario(
            g, planned, actual, flows, _args(router, sim_time)
        )
    return netsim


class CcsdsScenarioSmokeTests(unittest.TestCase):
    """Short integration runs of the vendored CCSDS reference scenarios."""

    def _smoke_run(self, scenario):
        g, planned, actual, flows = _load_scenario(scenario)
        self.assertEqual(len(g.nodes), EXPECTED_NODES[scenario])
        self.assertEqual(len(flows), EXPECTED_FLOWS[scenario])
        start = time.perf_counter()
        netsim = _run(g, planned, actual, flows, sim_time=SMOKE_SIM_TIME)
        walltime = time.perf_counter() - start
        self.assertEqual(len(netsim.nodes), EXPECTED_NODES[scenario])
        self.assertEqual(netsim.duration, SMOKE_SIM_TIME)
        # traffic must have been generated and the run must stay fast
        # (wall time budget as a performance regression tripwire)
        self.assertGreater(netsim.routing_stats["created"], 0)
        self.assertLess(
            walltime,
            120,
            "scenario smoke run got slower than 120s, possible simulation "
            "performance regression",
        )
        return netsim, walltime

    def test_lunar_scenario_smoke(self):
        # within the first 900 seconds the fixed eth links already carry
        # the control centre traffic
        netsim, _ = self._smoke_run("lunar-communication")
        self.assertGreater(netsim.routing_stats["delivered"], 0)
        self.assertGreater(netsim.net_stats["tx"], 0)

    def test_mars_scenario_smoke(self):
        self._smoke_run("mars-communication")

    def test_low_earth_orbit_scenario_smoke(self):
        self._smoke_run("low-earth-orbit")

    def test_leo_policy_file_is_reported_as_unsupported(self):
        with self.assertLogs("scenariohelper", level="WARNING") as logs:
            scenariohelper.load_scenario_dir(
                str(CCSDS / "low-earth-orbit" / "v1.0")
            )
        self.assertTrue(
            any("policy" in line for line in logs.output),
            "expected a warning that the LEO policy.json is ignored",
        )


class PlannedActualSemanticsTests(unittest.TestCase):
    """Tests for the planned contacts / actual contacts semantics."""

    def test_deliveries_with_actual_contacts_never_exceed_planned(self):
        # actual contacts are derived from planned contacts by shortening
        # and dropping, so routing on the actual data plane can never
        # deliver more than routing on the (optimistic) planned contacts;
        # the runs are seeded identically because the StaticRouter picks
        # random next hops between equal cost candidates
        for scenario in ["lunar-communication", "low-earth-orbit"]:
            with self.subTest(scenario=scenario):
                g, planned, actual, flows = _load_scenario(scenario)
                random.seed(7)
                planned_with_actual = _run(
                    g, planned, actual, flows, sim_time=SMOKE_SIM_TIME
                )
                random.seed(7)
                planned_as_actual = _run(
                    g, planned, planned, flows, sim_time=SMOKE_SIM_TIME
                )
                self.assertEqual(
                    planned_with_actual.routing_stats["created"],
                    planned_as_actual.routing_stats["created"],
                )
                self.assertLessEqual(
                    planned_with_actual.routing_stats["delivered"],
                    planned_as_actual.routing_stats["delivered"],
                )

    def test_planned_only_links_do_not_carry_traffic(self):
        # the planned contact window n2 -> n3 opens at 0 and again at 100,
        # the actual contact only exists at 100, so within the first 60
        # seconds nothing must reach n3 even though the router knows the
        # planned link (planned-only links are not always-on edges)
        td = _synthetic_planned_actual_scenario(
            planned_windows="0,30\n100,130",
            actual_windows="100,130",
        )
        self.addCleanup(td.cleanup)
        scenario_dir = td.name
        files = scenariohelper.load_scenario_dir(scenario_dir)
        mapping_obj = scenariohelper.load_mapping_json(files["nodes"])
        mapping = {k: v["node_number"] for k, v in mapping_obj.items()}
        planned = scenariorunner.read_contacts_file(files["planned_contacts"], mapping)
        actual = scenariorunner.read_contacts_file(files["actual_contacts"], mapping)
        flows = scenariohelper.load_application_traffic(files["traffic"], mapping_obj)
        g = scenariohelper.get_graph_from_contacts(planned, mapping_obj)
        g = nx.relabel_nodes(g, mapping)

        early = _run(g, planned, actual, flows, sim_time=60)
        self.assertGreater(early.routing_stats["created"], 0)
        self.assertEqual(early.routing_stats["delivered"], 0)

        # with the actual window in reach, the bundles go out
        late = _run(g, planned, actual, flows, sim_time=150)
        self.assertGreater(late.routing_stats["delivered"], 0)

        # and with the planned contacts as the data plane, the early
        # window already carries them
        optimistic = _run(g, planned, planned, flows, sim_time=60)
        self.assertGreater(optimistic.routing_stats["delivered"], 0)


class ScenarioRuntimeTests(unittest.TestCase):
    def test_sim_time_defaults_to_latest_finite_contact_end(self):
        # the simple test contacts end at 210, so the simulation must run
        # for exactly that long (not the fixed links' -1 end time)
        mapping_obj = scenariohelper.load_mapping_json(
            str(SIMPLE_TEST / "nodes.json")
        )
        mapping = {k: v["node_number"] for k, v in mapping_obj.items()}
        contacts = scenariorunner.read_contacts_file(
            str(SIMPLE_TEST / "contacts.csv"), mapping
        )
        g = nx.relabel_nodes(
            scenariohelper.get_graph_from_contacts(contacts, mapping_obj), mapping
        )
        flows = []
        netsim = _run(g, contacts, contacts, flows)
        self.assertEqual(netsim.duration, 210.0)

    def test_fixed_only_contact_plan_requires_sim_time(self):
        # a plan with only fixed 0,-1 contacts has no finite end to derive
        # the runtime from, so the run refuses to start
        mapping_obj = scenariohelper.load_mapping_json(
            str(SIMPLE_TEST / "nodes.json")
        )
        mapping = {k: v["node_number"] for k, v in mapping_obj.items()}
        contacts = scenariorunner.read_contacts_file(
            str(SIMPLE_TEST / "contacts.csv"), mapping
        )
        fixed_only = [c for c in contacts if c.fixed]
        self.assertTrue(len(fixed_only) > 0)
        g = nx.relabel_nodes(
            scenariohelper.get_graph_from_contacts(fixed_only, mapping_obj), mapping
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                scenariorunner.run_scenario(
                    g, fixed_only, fixed_only, [], _args("StaticRouter", None)
                )


def _synthetic_planned_actual_scenario(planned_windows: str, actual_windows: str):
    """Create a small CCSDS-format planned/actual scenario in a temp dir.

    Returns the tempfile.TemporaryDirectory (keep it alive while the
    scenario dir is used).
    """
    import tempfile

    tmpdir = tempfile.TemporaryDirectory()
    import json
    import os

    d = tmpdir.name
    with open(os.path.join(d, "nodes.json"), "w") as f:
        json.dump(
            [
                {"node_label": "n1", "node_name": "node1", "node_id": "ipn:1.0"},
                {"node_label": "n2", "node_name": "node2", "node_id": "ipn:2.0"},
                {"node_label": "n3", "node_name": "node3", "node_id": "ipn:3.0"},
            ],
            f,
        )
    with open(os.path.join(d, "traffic.json"), "w") as f:
        json.dump(
            [
                {
                    "info": "n1 [ipn:1.0] -> n3 [ipn:3.0]",
                    "src": "ipn:1.5",
                    "dst": "ipn:3.5",
                    "start_time": 0,
                    "end_time": -1,
                    "adu_size": 10_000,
                    "interval": 10,
                }
            ],
            f,
        )
    header = "source,destination,contact_start(s),contact_end(s),data_rate(bps),delay(s),link_type\n"
    fixed_links = "n1,n2,0,-1,100000000,0.010,eth\nn2,n1,0,-1,100000000,0.010,eth\n"
    with open(os.path.join(d, "planned_contacts.csv"), "w") as f:
        f.write(header)
        f.write(fixed_links)
        for window in planned_windows.splitlines():
            start, end = window.split(",")
            f.write(f"n2,n3,{start},{end},1000000,0.010,rf\n")
            f.write(f"n3,n2,{start},{end},1000000,0.010,rf\n")
    with open(os.path.join(d, "actual_contacts.csv"), "w") as f:
        f.write(header)
        f.write(fixed_links)
        for window in actual_windows.splitlines():
            start, end = window.split(",")
            f.write(f"n2,n3,{start},{end},1000000,0.010,rf\n")
            f.write(f"n3,n2,{start},{end},1000000,0.010,rf\n")
    return tmpdir


if __name__ == "__main__":
    unittest.main()
