import pathlib
import unittest

import networkx as nx

import pons

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"


class NetworkPlanTests(unittest.TestCase):
    def setUp(self):
        # node 1 -- (static link) -- node 2 -- (dynamic 30..60) -- node 3
        g = nx.MultiDiGraph()
        g.add_node(1, name="n1")
        g.add_node(2, name="n2")
        g.add_node(3, name="n3")
        g.add_edge(1, 2, bw=1_000_000, delay=0.01, loss=0.0, jitter=0.0)
        contacts = pons.ContactPlan(
            contacts=[
                pons.Contact(timespan=(30, 60), nodes=(2, 3), bw=100, delay=1),
                pons.Contact(timespan=(0, -1), nodes=(1, 3), bw=50, delay=2, fixed=True),
            ]
        )
        self.plan = pons.net.NetworkPlan(g, contacts=contacts)

    def test_static_graph(self):
        # dynamic contact edges are removed from the static graph, fixed
        # links of the contact plan are merged into it
        self.assertTrue(self.plan.G.has_edge(1, 2))
        self.assertFalse(self.plan.G.has_edge(2, 3))
        self.assertTrue(self.plan.G.has_edge(1, 3))
        self.assertEqual(sorted(self.plan.fixed_links()), [(1, 2), (1, 3)])

    def test_full_graph_contains_all_links(self):
        # the full graph is the routing knowledge: static AND dynamic links
        self.assertTrue(self.plan.full_graph.has_edge(1, 2))
        self.assertTrue(self.plan.full_graph.has_edge(2, 3))
        self.assertTrue(self.plan.full_graph.has_edge(1, 3))

    def test_has_contact(self):
        # static links are always up, dynamic ones only during their window
        self.assertTrue(self.plan.has_contact(0, 1, 2))
        self.assertTrue(self.plan.has_contact(10_000, 1, 3))  # fixed link merged into G
        self.assertFalse(self.plan.has_contact(0, 2, 3))
        self.assertTrue(self.plan.has_contact(45, 2, 3))
        self.assertFalse(self.plan.has_contact(61, 2, 3))
        # directional, no reverse contact (symmetric=False)
        self.assertFalse(self.plan.has_contact(45, 3, 2))

    def test_at_includes_static_links(self):
        at_45 = self.plan.at(45)
        nodes = {c.nodes for c in at_45}
        self.assertIn((1, 2), nodes)
        self.assertIn((1, 3), nodes)
        self.assertIn((2, 3), nodes)
        static = [c for c in at_45 if c.fixed]
        self.assertEqual(sorted(n.nodes for n in static), [(1, 2), (1, 3)])

    def test_connections_at_time(self):
        at_0 = self.plan.connections_at_time(0)
        at_45 = self.plan.connections_at_time(45)
        self.assertEqual(sorted(set(at_0)), [(1, 2), (1, 3)])
        self.assertEqual(sorted(set(at_45)), [(1, 2), (1, 3), (2, 3)])

    def test_nodes(self):
        self.assertEqual(sorted(self.plan.nodes()), [1, 2, 3])

    def test_generate_nodes(self):
        nodes = self.plan.generate_nodes(router=pons.routing.DirectDeliveryRouter())
        self.assertEqual(len(nodes), 3)
        # nodes carry the network plan and their router got the node id
        for node in nodes:
            self.assertIn("contactplan", node.net)
            self.assertEqual(node.router.my_id, node.node_id)

    def test_from_graphml(self):
        plan = pons.net.NetworkPlan.from_graphml(
            str(EXAMPLES / "data" / "3n-dyn-link.graphml")
        )
        self.assertEqual(sorted(plan.nodes()), [1, 2, 3])
        # the dynamic link (2,3) is removed from the static graph,
        # the static link (1,2) stays
        self.assertTrue(plan.G.has_edge(1, 2))
        self.assertFalse(plan.G.has_edge(2, 3))


if __name__ == "__main__":
    unittest.main()
