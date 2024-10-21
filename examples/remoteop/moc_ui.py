#!/usr/bin/env python3

import sys
from nicegui import ui, run

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
            ui.label("50")
        with ui.row():
            ui.label("Y:")
            ui.label("50")
        with ui.row():
            ui.label("Direction:")
            knob = ui.knob(value=45, min=0, max=360, step=1, show_value=True)
            knob.enabled = False
    with ui.tab_panel(pwr):
        ui.label("Power")
    with ui.tab_panel(payload):
        ui.label("Payload")
    with ui.tab_panel(cmd):
        ui.label("Commands")
    with ui.tab_panel(dbg):
        ui.label("Debug")

ui.run(title="Rover1 Mission Control", dark=True)
