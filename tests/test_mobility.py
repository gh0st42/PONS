import pathlib
import random
import unittest

from pons import OneMovement, generate_randomwaypoint_movement

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"


class RandomWaypointTests(unittest.TestCase):
    def test_movement_generation(self):
        random.seed(42)
        moves = generate_randomwaypoint_movement(100, 5, 300, 300)
        # one initial position per node plus the waypoints
        self.assertGreaterEqual(len(moves), 5)
        self.assertTrue(all(m[1] < 5 for m in moves))
        # the first move of each node is at time 0
        first = {(m[1], m[0]) for m in moves}
        for node_id in range(5):
            self.assertIn((node_id, 0.0), first)
        # moves are timestamped within the scenario duration
        self.assertTrue(all(m[0] <= 100 for m in moves))

    def test_movement_is_seeded(self):
        random.seed(123)
        a = generate_randomwaypoint_movement(100, 5, 300, 300)
        random.seed(123)
        b = generate_randomwaypoint_movement(100, 5, 300, 300)
        self.assertEqual(a, b)
        random.seed(124)
        c = generate_randomwaypoint_movement(100, 5, 300, 300)
        self.assertNotEqual(a, c)


class OneMovementTests(unittest.TestCase):
    def test_from_file(self):
        movement = OneMovement.from_file(str(EXAMPLES / "data" / "scenario1.one"))
        self.assertEqual(movement.duration, 3600.0)
        self.assertGreater(movement.num_nodes, 0)
        self.assertGreater(len(movement.moves), 0)
        # all nodes have their first position at time 0
        first_times = {}
        for time, node_id, *_ in movement.moves:
            if node_id not in first_times or time < first_times[node_id]:
                first_times[node_id] = time
        self.assertEqual(set(first_times.values()), {0.0})

    def test_str(self):
        movement = OneMovement.from_file(str(EXAMPLES / "data" / "scenario1.one"))
        self.assertIn("OneMovement(", str(movement))


if __name__ == "__main__":
    unittest.main()
