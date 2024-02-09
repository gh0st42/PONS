import math
from pathlib import Path
import unittest

from pons import Ns2Movement


class Ns2Tests(unittest.TestCase):
    """
    tests for ns2 movement
    """
    # further test files must be of the same format
    # ns2_example_<start_time>_<end_time>_<first_entry>_<last_entry>.txt
    # start_time: the start time of the scenario
    # end_time: the end time of the scenario
    # first_entry: the floor of the first entry time
    # last_entry: the floor of the last entry time
    TESTFILES = [
        "ns2_example_0_3600_18_3035.txt",
        "ns2_example_-500_3600_-482_3508.txt",
        # this is commented, because it takes a long time to run
        # "ns2_example_0_43200_18_43167.txt"
    ]

    def test_metadata(self):
        """
        tests for correct metadata such as num_nodes, start and end time
        """
        for file in self.TESTFILES:
            splitted = file.split("_")
            start_time = int(splitted[2])
            end_time = int(splitted[3])
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file, start_time=start_time, end_time=end_time)
            self.assertEqual(movement.num_nodes, 3)
            self.assertEqual(movement.start, start_time)
            self.assertEqual(movement.end, end_time - 1)

    def test_contains_full_seconds(self):
        """
        tests if a move for each node and for each integer time between the start and end time exists
        """
        for file in self.TESTFILES:
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file)
            moves = movement.moves
            time_node_pairs = [(move[0], move[1]) for move in moves]
            for time in range(movement.start, math.floor(movement.end + 1)):
                for node in range(0, movement.num_nodes):
                    self.assertIn((time, node), time_node_pairs)

    def test_with_end_time(self):
        """
        tests if moves are generated correctly until the given end time
        """
        for file in self.TESTFILES:
            duration = int(file.split("_")[3])
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file, end_time=duration)
            moves = movement.moves
            time_node_pairs = [(move[0], move[1]) for move in moves]
            for time in range(movement.start, 3600):
                for node in range(0, movement.num_nodes):
                    self.assertIn((time, node), time_node_pairs)

    def test_stop_early(self):
        """
        tests if moves are generated correctly until the given end time
        """
        end_time = 20
        for file in self.TESTFILES:
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file, end_time=end_time)
            moves = movement.moves
            self.assertLessEqual(max(move[0] for move in moves), end_time)

    def test_with_start_time(self):
        """
        tests if moves are generated correctly until the given end time
        """
        for file in self.TESTFILES:
            start = int(file.split("_")[2])
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file, start_time=start)
            moves = movement.moves
            time_node_pairs = [(move[0], move[1]) for move in moves]
            for time in range(start, math.floor(movement.end)):
                for node in range(0, movement.num_nodes):
                    self.assertIn((time, node), time_node_pairs)

    def test_start_late(self):
        """
        tests if moves are generated correctly until the given end time
        """
        start_time = 30
        for file in self.TESTFILES:
            source_path = Path(__file__).resolve()
            source_dir = source_path.parent
            file = source_dir.joinpath(file)
            movement = Ns2Movement.from_file(file, start_time=start_time)
            moves = movement.moves
            self.assertEqual(start_time, min(move[0] for move in moves))


if __name__ == "__main__":
    unittest.main()