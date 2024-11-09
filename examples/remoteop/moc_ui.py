#!/usr/bin/env python3

import sys
from nicegui import ui, run
import requests
import json

ui.markdown("### Rover1 Mission Control")

status = ui.label("Last TM HK received: n/a")

with ui.tabs().classes("w-full") as tabs:
    pos = ui.tab("Position")
    pwr = ui.tab("Power")
    payload = ui.tab("Payload")
    cmd = ui.tab("Commands")
    dbg = ui.tab("Debug")

with ui.tab_panels(tabs, value=pos).classes("w-full"):
    with ui.tab_panel(pos):
        ui.label("Position")
        with ui.row():
            ui.label("X:")
            lbl_x = ui.label("50")
        with ui.row():
            ui.label("Y:")
            lbl_y = ui.label("50")
        with ui.row():
            ui.label("Direction:")
            knob_dir = ui.knob(value=45, min=0, max=360, step=1, show_value=True)
            knob_dir.enabled = False
    with ui.tab_panel(pwr):
        ui.label("Power")
    with ui.tab_panel(payload):
        ui.label("Payload")
    with ui.tab_panel(cmd):
        ui.label("Commands")
    with ui.tab_panel(dbg):
        ui.label("Debug")


def update_position_from_latest():
    global last_tm
    if last_tm is not None:
        print(last_tm)
        tm = last_tm["data"]
        print("TM", tm)
        x = float(tm["position"][0])
        y = float(tm["position"][1])
        direction = float(tm["direction"])
        lbl_x.set_text("%.02f" % x)
        lbl_y.set_text("%.02f" % y)
        knob_dir.value = direction


last_tm = None
highest_tm_id = 0
tm_history = {}


async def on_timer():
    global status
    global last_tm
    global highest_tm_id
    global tm_history

    print("timer")
    URL = "http://localhost:18080/read/tmbuf"
    response = await run.io_bound(requests.get, URL, timeout=1)
    print(response.text)
    if response.status_code == 200:
        tmbuf = response.text.split("\n")
        for tm in tmbuf:
            hdr, tm_data = tm.split("|", 1)
            tm_data = tm_data.strip()
            ts, src, tm_id_str, size = hdr.strip().split(" ")
            ts = float(ts)
            src = int(src)
            size = int(size)
            tm_id_fields = tm_id_str.split("-")
            tm_id = int(tm_id_fields[2])
            tm_history[tm_id] = {
                "ts": ts,
                "src": src,
                "size": size,
                "id": tm_id,
                "tm_id_str": tm_id_str,
                "data": json.loads(tm_data),
            }

            if tm_id <= highest_tm_id:
                continue
            highest_tm_id = tm_id

            last_tm = {
                "ts": ts,
                "src": src,
                "size": size,
                "id": tm_id,
                "tm_id_str": tm_id_str,
                "data": json.loads(tm_data),
            }

            status.set_text("Latest TM HK received: %.02f" % float(ts))
            update_position_from_latest()
            print(tm_data)

    # status.set_text("Last TM HK received: %d" % 42)


timer = ui.timer(1, lambda: on_timer())
ui.run(title="Rover1 Mission Control", dark=True)
