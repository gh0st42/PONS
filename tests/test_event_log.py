import json
import os
import tempfile
import unittest

from pons import event_log as ev


class EventLogTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.logfile = os.path.join(self.tmpdir.name, "events.log")
        ev.event_log_fh = None
        ev.event_filter = []

    def tearDown(self):
        ev.event_filter = []
        if ev.event_log_fh is not None:
            ev.close_log()
        self.tmpdir.cleanup()

    def _write_events(self):
        ev.open_log(self.logfile)
        ev.event_log(4.0, "BUNDLE", {"event": "created", "id": "M1"})
        ev.event_log(9.5, "NET", {"event": "TX", "id": "M1"})
        ev.event_log(14.0, "BUNDLE", {"event": "delivered", "id": "M1"})
        ev.close_log()

    def test_open_write_close(self):
        self.assertFalse(ev.is_logging())
        self._write_events()
        self.assertFalse(ev.is_logging())
        with open(self.logfile) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 3)
        ts, category, msg = lines[0].split(maxsplit=2)
        self.assertEqual(float(ts), 4.0)
        self.assertEqual(category, "BUNDLE")
        self.assertEqual(json.loads(msg), {"event": "created", "id": "M1"})

    def test_event_filter_suppresses_categories(self):
        ev.open_log(self.logfile)
        ev.event_filter = ["NET"]
        ev.event_log(4.0, "BUNDLE", {"event": "created", "id": "M1"})
        ev.event_log(9.5, "NET", {"event": "TX", "id": "M1"})
        ev.close_log()
        with open(self.logfile) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("BUNDLE", lines[0])

    def test_load_event_log_filters_and_max_ts(self):
        self._write_events()
        # the event at 9.5 rounds up to slot 10 and hits the max_ts=10
        # cutoff, which aborts loading (events are expected to be sorted
        # by time), so the 14.0 event is never reached
        events, max_time = ev.load_event_log(
            self.logfile, filter_in=["BUNDLE", "NET"], max_ts=10.0
        )
        self.assertEqual(max_time, 4)
        self.assertEqual(len(events[4]), 1)
        self.assertEqual(events[4][0][2]["event"], "created")
        # without a cutoff all events are loaded
        events, max_time = ev.load_event_log(
            self.logfile, filter_in=["BUNDLE", "NET"]
        )
        all_events = [e for slot in events.values() for e in slot]
        self.assertEqual(len(all_events), 3)
        self.assertEqual(max_time, 14)

    def test_load_event_log_filter_out(self):
        self._write_events()
        events, _ = ev.load_event_log(
            self.logfile, filter_in=["NET", "BUNDLE"], filter_out=["NET"]
        )
        # NET is excluded, both BUNDLE events remain
        all_events = [e for slot in events.values() for e in slot]
        self.assertEqual(len(all_events), 2)
        self.assertTrue(all(e[1] == "BUNDLE" for e in all_events))


if __name__ == "__main__":
    unittest.main()
