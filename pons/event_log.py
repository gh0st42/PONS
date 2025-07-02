from json import dumps, loads
from typing import Tuple

event_log_fh = None
event_filter = []


def is_logging() -> bool:
    global event_log_fh
    return event_log_fh is not None


def open_log(filename: str = "/tmp/events.log"):
    global event_log_fh
    event_log_fh = open(filename, "w")


def event_log(ts: float, category: str, msg: dict):
    global event_log_fh
    global event_filter

    for f in event_filter:
        if f == category:
            return

    if event_log_fh is not None:
        event_log_fh.write("%f %s %s\n" % (ts, category, dumps(msg)))
        event_log_fh.flush()


def close_log():
    global event_log_fh
    if event_log_fh is not None:
        event_log_fh.close()
        event_log_fh = None


def load_event_log(
    filename: str = "/tmp/events.log", filter_out: list = [], filter_in: list = []
) -> Tuple[dict, float]:
    events = {}
    max_time = 0
    with open(filename) as fh:
        for line in fh.readlines():
            ts, category, msg = line.strip().split(maxsplit=2)
            ts_slot = round(float(ts))
            max_time = max(max_time, int(ts_slot))
            if category in filter_out:
                continue
            if category in filter_in:
                # round ts to 1 decimal
                if ts_slot not in events.keys():
                    events[ts_slot] = []
                events[ts_slot].append((float(ts), category, loads(msg)))
    return (events, max_time)


def get_events_in_range(
    events: dict, start: float, end: float, filter_out=[], filter_in=[]
):
    result = []
    for ts, e in events.items():
        if ts < start or ts > end:
            continue
        for ee in e:
            if ee[1] in filter_out:
                continue
            if len(filter_in) > 0 and ee[1] not in filter_in:
                continue
            if ee[0] >= start and ee[0] <= end:
                result.append(ee)
    return result
