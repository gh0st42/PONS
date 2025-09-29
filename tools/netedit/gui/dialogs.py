from tkinter import *
from tkinter import ttk


def add_label_entry(frame, text, row, default_value=""):
    textvar = StringVar()
    textvar.set(default_value)

    subframe = frame
    # subframe = ttk.Frame(frame)
    label = ttk.Label(subframe, text=text)
    label.grid(row=row, column=0, padx=10, pady=10)
    entry = ttk.Entry(subframe, textvariable=textvar)
    entry.grid(row=row, column=1, padx=10, pady=10)
    # subframe.pack()
    # textvar.trace_add("write", prop_changed)
    return textvar


def add_label_checkbox(frame, text, row, default_value=False):
    textvar = BooleanVar()
    textvar.set(default_value)

    subframe = frame
    # subframe = ttk.Frame(frame)
    label = ttk.Label(subframe, text=text)
    label.grid(row=row, column=0, padx=10, pady=10)
    entry = ttk.Checkbutton(subframe, variable=textvar)
    entry.grid(row=row, column=1, padx=10, pady=10)
    # subframe.pack()
    # textvar.trace_add("write
    return textvar


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


def dialog_link_properties(n1, n2, graph):
    link_data = graph.get_edge_data(n1, n2)
    if not "bw" in link_data:
        link_data["bw"] = 0
    if not "delay" in link_data:
        link_data["delay"] = 0
    if not "jitter" in link_data:
        link_data["jitter"] = 0
    if not "loss" in link_data:
        link_data["loss"] = 0
    if not "dynamic_link" in link_data:
        link_data["dynamic_link"] = False

    print("link properties")
    dialog_link_prop = Toplevel()
    dialog_link_prop.title("Link : %s - %s" % (n1, n2))
    dialog_link_prop.geometry("400x300")
    # dialog_setup.transient(root)
    dialog_link_prop.grab_set()

    subframe = ttk.Frame(dialog_link_prop)

    bw = add_label_entry(subframe, "Bandwidth", 0, default_value=str(link_data["bw"]))
    delay = add_label_entry(
        subframe, "Delay (in ms)", 1, default_value=str(link_data["delay"])
    )
    jitter = add_label_entry(
        subframe, "Jitter (in ms)", 2, default_value=str(link_data["jitter"])
    )
    loss = add_label_entry(
        subframe, "Loss (in %)", 3, default_value=str(link_data["loss"])
    )
    dynamic_link = add_label_checkbox(
        subframe, "Dynamic Link", 4, default_value=link_data["dynamic_link"]
    )
    subframe.pack(padx=5, pady=5)

    # canvas_height = ttk.Entry(size_frame)
    # canvas_height.pack(side=LEFT, padx=5)
    # canvas_height.insert(0, str(h))
    # size_frame.pack()

    bottom_row = ttk.Frame(dialog_link_prop)

    def apply():
        bw2 = int(
            bw.get()
            .replace(" ", "")
            .replace("mbit", "000000")
            .replace("kbit", "000")
            .replace("gbit", "000000000")
        )
        print(bw2)
        delay2 = float(delay.get())
        print(delay.get())
        jitter2 = float(jitter.get())
        print(jitter.get())
        loss2 = float(loss.get())
        print(loss.get())
        link_data["bw"] = bw2
        link_data["delay"] = delay2
        link_data["jitter"] = jitter2
        link_data["loss"] = loss2
        link_data["dynamic_link"] = dynamic_link.get()
        graph.edges[n1, n2].update(link_data)

        dialog_link_prop.destroy()

    ttk.Button(bottom_row, text="Apply", command=apply).pack(side=RIGHT)
    ttk.Button(bottom_row, text="Cancel", command=dialog_link_prop.destroy).pack(
        side=RIGHT
    )
    bottom_row.pack(padx=5, pady=5)
    return dialog_link_prop
