import json
import pathlib
import subprocess
import sys
import unittest

EXAMPLES_DIR = pathlib.Path(__file__).parent.parent / "examples"
TESTS_JSON = EXAMPLES_DIR / "tests.json"


def json_objects_from_output(text: str) -> list:
    """Extract all JSON objects printed to stdout by an example script.

    The simulator prints progress bars and log lines around the stats
    blocks, so the objects are scanned out of the text instead of
    parsing the output as a whole.
    """
    dec = json.JSONDecoder()
    objects = []
    pos = 0
    while pos < len(text):
        if text[pos] == "{":
            try:
                obj, end = dec.raw_decode(text, pos)
                objects.append(obj)
                pos = end
                continue
            except json.JSONDecodeError:
                pass
        newline = text.find("\n", pos)
        if newline == -1:
            break
        pos = newline + 1
    return objects


class ExampleTests(unittest.TestCase):
    """Run the example scripts and check their expected results.

    The expected results live in examples/tests.json, the same file used
    by examples/run_tests. Dict conditions must be matched by one JSON
    stats block in the output, string conditions must appear as a
    substring of the output.
    """

    @classmethod
    def setUpClass(cls):
        with open(TESTS_JSON, "r") as f:
            cls.tests = json.load(f)

    def _run_example(self, filename: str) -> str:
        proc = subprocess.run(
            [sys.executable, str(filename)],
            cwd=EXAMPLES_DIR,
            capture_output=True,
            timeout=300,
        )
        if proc.returncode != 0:
            self.fail(
                f"Example {filename} failed with exit code {proc.returncode}:\n"
                f"{proc.stdout.decode()[-2000:]}\n{proc.stderr.decode()[-2000:]}"
            )
        return proc.stdout.decode()

    def test_examples(self):
        self.assertGreater(len(self.tests), 0)
        for test in self.tests:
            filename = test["file"]
            with self.subTest(example=filename):
                output = self._run_example(filename)

                for condition in test.get("results", []):
                    if isinstance(condition, str):
                        self.assertIn(
                            condition,
                            output,
                            f"Expected substring '{condition}' not printed by {filename}",
                        )
                    else:
                        stats = json_objects_from_output(output)
                        self.assertTrue(
                            any(
                                all(
                                    key in obj and str(obj[key]) == str(value)
                                    for key, value in condition.items()
                                )
                                for obj in stats
                            ),
                            f"Expected stats block {condition} not found in the output of "
                            f"{filename}. Printed stats: {stats}",
                        )


if __name__ == "__main__":
    unittest.main()
