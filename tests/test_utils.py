import unittest

from pons.message import Message
from pons.utils.list_utils import to_lookup, contains
from pons.utils.misc import flatten, get_marks_dict
from pons.utils.vector import Vector


class ListUtilsTests(unittest.TestCase):
    def test_to_lookup(self):
        lookup = to_lookup([1, 2, 3, 4], lambda v: v % 2)
        self.assertEqual(lookup[0], [2, 4])
        self.assertEqual(lookup[1], [1, 3])

    def test_contains(self):
        self.assertTrue(contains([1, 2, 3], lambda v: v == 2))
        self.assertFalse(contains([1, 2, 3], lambda v: v == 5))


class MiscTests(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten([1, [2, [3, 4]], 5]), [1, 2, 3, 4, 5])
        self.assertEqual(flatten([]), [])
        self.assertEqual(flatten("x"), ["x"])
        self.assertEqual(flatten(1), [1])

    def test_get_marks_dict(self):
        self.assertEqual(get_marks_dict(0, 10, 5), {0: "0", 5: "5", 10: "10"})
        self.assertEqual(get_marks_dict(0, 10, 1)[5], "5")


class VectorTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(Vector(1, 2) + Vector(3, 4), Vector(4, 6))
        self.assertEqual(Vector(3, 4) - Vector(1, 2), Vector(2, 2))
        self.assertEqual(Vector(1, 2) * 3, Vector(3, 6))
        self.assertEqual(Vector(4, 6) / 2, Vector(2, 3))
        self.assertEqual(2 * Vector(1, 1), Vector(2, 2))

    def test_abs_and_eq(self):
        self.assertEqual(abs(Vector(3, 4)), 5)
        self.assertTrue(Vector(1, 2) == Vector(1, 2))
        self.assertTrue(Vector(0, 0) == 0)

    def test_normalize(self):
        self.assertEqual(Vector(3, 4).normalize(), Vector(0.6, 0.8))
        # the zero vector stays the zero vector
        self.assertEqual(Vector(0, 0).normalize(), Vector(0, 0))

    def test_str(self):
        self.assertEqual(str(Vector(1, 2)), "Vector(1, 2)")
        self.assertEqual(repr(Vector(1, 2)), "Vector(1, 2)")


class MessageTests(unittest.TestCase):
    def test_message_fields_and_str(self):
        msg = Message(id="M", src=1, dst=2, size=100, created=0.0, ttl=10)
        self.assertEqual(
            str(msg), "Message(M, src=1.0, dst=2.0, size=100)"
        )

    def test_unique_id(self):
        msg = Message(id="M", src=1, dst=2, size=100, created=5.0)
        self.assertEqual(msg.unique_id(), "M-1-5")

    def test_is_expired(self):
        msg = Message(id="M", src=1, dst=2, size=100, created=10.0, ttl=30)
        self.assertFalse(msg.is_expired(39.9))
        self.assertTrue(msg.is_expired(40.1))

    def test_is_dtn_bundle(self):
        msg = Message(id="M", src=1, dst=2, size=100, created=0.0)
        self.assertTrue(msg.is_dtn_bundle())
        self.assertTrue(msg.is_dtn_bundle())  # even with no metadata
        plain = Message(id="M", src=1, dst=2, size=100, created=0.0, metadata=None)
        self.assertTrue(plain.is_dtn_bundle())
        non_bundle = Message(
            id="M", src=1, dst=2, size=100, created=0.0, metadata={"is_bundle": False}
        )
        self.assertFalse(non_bundle.is_dtn_bundle())


if __name__ == "__main__":
    unittest.main()
