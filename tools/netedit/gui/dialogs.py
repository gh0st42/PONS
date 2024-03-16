from tkinter import *
from tkinter import ttk


def dialog_setup(w, h):
    global canvas_w, canvas_h

    print("setup topology")
    dialog_setup = Toplevel()
    dialog_setup.title("Setup Topology")
    dialog_setup.geometry("400x300")
    # dialog_setup.transient(root)
    dialog_setup.grab_set()

    ttk.Label(dialog_setup, text="Canvas Size").pack(pady=5)
    size_frame = ttk.Frame(dialog_setup)
    canvas_width = ttk.Entry(size_frame)
    canvas_width.pack(side=LEFT, padx=5)
    canvas_width.insert(0, str(w))
    ttk.Label(size_frame, text="x").pack(side=LEFT)
    canvas_height = ttk.Entry(size_frame)
    canvas_height.pack(side=LEFT, padx=5)
    canvas_height.insert(0, str(h))
    size_frame.pack()

    bottom_row = ttk.Frame(dialog_setup)
    ttk.Button(bottom_row, text="Apply", command=dialog_setup.destroy).pack(side=RIGHT)
    ttk.Button(bottom_row, text="Cancel", command=dialog_setup.destroy).pack(side=RIGHT)
    bottom_row.pack(padx=5, pady=5)
