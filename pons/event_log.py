event_log_fh = None


def open_log(filename: str = "/tmp/events.log"):
    global event_log_fh
    event_log_fh = open(filename, "w")


def event_log(ts: float, category: str, msg: str):
    global event_log_fh

    if event_log_fh is not None:
        event_log_fh.write("[ %f ] [%s] %s\n" % (ts, category, msg))


def close_log():
    global event_log_fh
    if event_log_fh is not None:
        event_log_fh.close()
        event_log_fh = None
