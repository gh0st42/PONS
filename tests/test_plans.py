import pathlib
import unittest

from pons import Contact, ContactPlan, IonContactPlan
from pons.net.plans import bandwidth_parser
from pons.net.plans.parser import read_csv, read_json, read_ccp

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"
SIMPLE_TEST = EXAMPLES / "scenario" / "simple_test"
CCSDS_LUNAR = EXAMPLES / "scenarios" / "ccsds" / "lunar-communication" / "v1.0"


class BandwidthParserTests(unittest.TestCase):
    def test_suffixes_and_raw_values(self):
        self.assertEqual(bandwidth_parser("100mbit"), 100_000_000)
        self.assertEqual(bandwidth_parser("64kbit"), 64_000)
        self.assertEqual(bandwidth_parser("2gbit"), 2_000_000_000)
        self.assertEqual(bandwidth_parser("100mbit".upper()), 100_000_000)
        self.assertEqual(bandwidth_parser("5000000"), 5_000_000)
        self.assertEqual(bandwidth_parser(5000000), 5000000)

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            bandwidth_parser("not-a-bandwidth")


class ContactPlanTests(unittest.TestCase):
    def setUp(self):
        self.contacts = [
            Contact(timespan=(0, 10), nodes=(1, 2), bw=1000, delay=20),
            Contact(timespan=(20, 30), nodes=(1, 3), bw=2000, delay=30),
        ]
        self.plan = ContactPlan(contacts=list(self.contacts))

    def test_at_returns_active_contacts(self):
        self.assertEqual(len(self.plan.at(5)), 1)
        self.assertEqual(self.plan.at(5)[0].nodes, (1, 2))
        # window boundaries are inclusive
        self.assertEqual(len(self.plan.at(0)), 1)
        self.assertEqual(len(self.plan.at(10)), 1)
        self.assertEqual(len(self.plan.at(11)), 0)
        self.assertEqual(len(self.plan.at(25)), 1)
        self.assertEqual(self.plan.at(25)[0].nodes, (1, 3))

    def test_has_contact_is_directional_by_default(self):
        self.assertTrue(self.plan.has_contact(5, 1, 2))
        self.assertFalse(self.plan.has_contact(5, 2, 1))
        self.assertFalse(self.plan.has_contact(15, 1, 2))

    def test_has_contact_symmetric_accepts_reverse_direction(self):
        plan = ContactPlan(contacts=list(self.contacts), symmetric=True)
        self.assertTrue(plan.has_contact(5, 1, 2))
        self.assertTrue(plan.has_contact(5, 2, 1))
        self.assertTrue(plan.has_contact(25, 3, 1))

    def test_tx_time_for_contact(self):
        # size/bw plus delay and jitter of the matching contact
        tx_time = self.plan.tx_time_for_contact(5, 1, 2, 1000)
        self.assertAlmostEqual(tx_time, 1000 / 1000 + 20 / 1000)
        with self.assertRaises(Exception):
            self.plan.tx_time_for_contact(5, 2, 1, 1000)  # wrong direction
        with self.assertRaises(Exception):
            self.plan.tx_time_for_contact(15, 1, 2, 1000)  # no active contact

    def test_next_event_returns_next_boundary(self):
        self.assertEqual(self.plan.next_event(0), 10)
        self.assertEqual(self.plan.next_event(11), 20)
        self.assertEqual(self.plan.next_event(30), None)

    def test_fixed_links_and_max_time(self):
        plan = ContactPlan(
            contacts=[
                Contact(timespan=(0, -1), nodes=(1, 2), fixed=True),
                Contact(timespan=(10, 55), nodes=(2, 3)),
            ]
        )
        self.assertEqual(plan.fixed_links(), [(1, 2)])
        self.assertEqual(plan.get_max_time(), 55)
        self.assertTrue(plan.has_contact(20, 2, 3))
        # NOTE: a fixed contact never matches at() because of its -1 end
        # time; it becomes an always-on link only once NetworkPlan merges
        # it into the static graph (see the NetworkPlan tests)
        self.assertFalse(plan.has_contact(1_000_000, 1, 2))

    def test_all_contacts(self):
        self.assertEqual(
            sorted(self.plan.all_contacts()), sorted([(1, 2), (1, 3)])
        )


class ContactParserTests(unittest.TestCase):
    """Tests for the contact file readers with the repo's example data."""

    def setUp(self):
        self.mapping = {"n1": 1, "n2": 2, "n3": 3}

    def test_read_csv(self):
        contacts = read_csv(
            str(SIMPLE_TEST / "contacts.csv"), mapping=self.mapping
        )
        self.assertEqual(len(contacts), 10)
        fixed = [c for c in contacts if c.fixed]
        self.assertEqual(len(fixed), 2)  # the eth links, end time -1
        self.assertTrue(all(c.bw > 0 for c in contacts))
        self.assertIn(Contact(timespan=(0, 30), nodes=(2, 3), bw=2_000_000, delay=0.01),contacts)

    def test_read_csv_skips_rows_with_unknown_nodes(self):
        # rows referencing unknown nodes are logged and skipped,
        # not errors, so a wrong mapping yields an empty plan
        contacts = read_csv(str(SIMPLE_TEST / "contacts.csv"), mapping={})
        self.assertEqual(contacts, [])

    def test_read_json(self):
        contacts = read_json(
            str(SIMPLE_TEST / "contacts.json"), mapping=self.mapping
        )
        self.assertEqual(len(contacts), 10)
        self.assertEqual(sorted(c.nodes for c in contacts),
                         sorted([c.nodes for c in read_csv(
                             str(SIMPLE_TEST / "contacts.csv"), mapping=self.mapping)]))

    def test_read_ccp(self):
        contacts = read_ccp(
            str(SIMPLE_TEST / "contacts.ccp"), mapping=self.mapping
        )
        self.assertEqual(len(contacts), 10)

    def test_all_readers_agree(self):
        """CSV, JSON and CCP descriptions of the same plan must be equal."""
        csv_contacts = read_csv(str(SIMPLE_TEST / "contacts.csv"), mapping=self.mapping)
        json_contacts = read_json(
            str(SIMPLE_TEST / "contacts.json"), mapping=self.mapping
        )
        ccp_contacts = read_ccp(
            str(SIMPLE_TEST / "contacts.ccp"), mapping=self.mapping
        )
        self.assertEqual(len(csv_contacts), 10)
        self.assertEqual(csv_contacts, json_contacts)
        self.assertEqual(csv_contacts, ccp_contacts)

    def test_read_ccp_core_example(self):
        contacts = read_ccp(str(EXAMPLES / "data" / "3n.ccm"))
        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[0].timespan, (30.0, 60.0))
        self.assertEqual(contacts[0].nodes, (0, 1))
        self.assertEqual(contacts[1].timespan, (60.0, 90.0))

    def test_read_csv_ccsds_planned_contacts(self):
        """The CCSDS reference scenario CSVs parse with raw bps rates."""
        mapping = {
            "lbcc": 10,
            "lrcc": 20,
            "lucc": 30,
            "lb": 11,
            "lrov": 21,
            "lgwu": 31,
            "lrec1": 100,
            "lrec2": 200,
            "lgs1": 110,
            "lgs2": 210,
            "lgs3": 211,
            "lgw": 220,
            "lre1": 120,
            "lre2": 221,
        }
        contacts = read_csv(
            str(CCSDS_LUNAR / "planned_contacts.csv"), mapping=mapping
        )
        self.assertGreater(len(contacts), 100)
        # always-on links (eth segment) come with end time -1
        fixed = [c for c in contacts if c.fixed]
        self.assertGreater(len(fixed), 20)
        self.assertIn((10, 100), [c.nodes for c in fixed])
        # dynamic rates are plain bps integers in the CCSDS format
        dynamic = [c for c in contacts if not c.fixed]
        self.assertTrue(all(c.bw > 0 for c in dynamic))
        rates = {c.bw for c in dynamic}
        self.assertEqual(rates, {15_000_000, 30_000_000, 100_000_000})


class IonContactPlanTests(unittest.TestCase):
    def test_from_file(self):
        plan = IonContactPlan.from_file(
            str(EXAMPLES / "data" / "contactPlan_simple.txt")
        )
        self.assertEqual(len(plan.contacts), 2)
        self.assertTrue(plan.has_contact(100, 0, 1))
        self.assertTrue(plan.has_contact(100, 1, 0))
        self.assertFalse(plan.has_contact(300, 0, 1))
        self.assertEqual(plan.contacts[0].timespan, (0.0, 200.0))


if __name__ == "__main__":
    unittest.main()
