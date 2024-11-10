#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk
from tkinter import messagebox, filedialog
import networkx as nx
import sys
import os
from PIL import Image, ImageTk

if __name__ == "__main__":
    from gui.dialogs import *
else:
    from .gui.dialogs import *

next_node_num = 1
selected_node = 0

current_filename = ""

graph = nx.Graph()

active_tool = "Node"

background_image = None

if os.environ.get("BG_IMG"):
    background_image = os.environ.get("BG_IMG")

canvas_w = 2000
canvas_h = 2000


def focus_in(event):
    global root
    root.unbind("1")
    root.unbind("2")
    root.unbind("3")
    root.unbind("4")


def focus_out(event):
    global root
    root.bind("1", lambda e: toolbtn_click(btns[0], btns))
    root.bind("2", lambda e: toolbtn_click(btns[1], btns))
    root.bind("3", lambda e: toolbtn_click(btns[2], btns))
    root.bind("4", lambda e: toolbtn_click(btns[3], btns))


def add_label_entry(frame, text, row):
    textvar = StringVar()
    # subframe = ttk.Frame(frame)
    subframe = frame
    label = ttk.Label(subframe, text=text)
    label.grid(row=row, column=0, padx=10, pady=10)
    entry = ttk.Entry(subframe, textvariable=textvar)
    entry.bind("<FocusIn>", focus_in)
    entry.bind("<FocusOut>", focus_out)
    entry.grid(row=row, column=1, padx=10, pady=10)
    # subframe.pack()
    # textvar.trace_add("write", prop_changed)
    entry.bind("<FocusOut>", prop_changed)
    entry.bind("<Return>", prop_changed)
    return textvar


def update_ui():
    global canvas
    global frame_links
    global img
    global background_image

    canvas.delete("all")
    if background_image is not None:
        canvas.create_image(0, 0, image=img, anchor=NW)

    draw_links()
    draw_nodes()
    draw_prop_links(frame_links)
    update_status()

    # update properties based on selected node
    if selected_node != 0:
        prop_name.set(graph.nodes[selected_node]["name"])
        prop_nodeid.set(selected_node)
        prop_x.set(graph.nodes[selected_node]["x"])
        prop_y.set(graph.nodes[selected_node]["y"])
    else:
        prop_name.set("")
        prop_nodeid.set("")
        prop_x.set("")
        prop_y.set("")


def update_status():
    global graph
    global statusNodesVar
    global statusLinksVar
    statusNodesVar.set(len(graph.nodes))
    statusLinksVar.set(len(graph.edges))


def draw_links():
    global graph
    global canvas

    nodes = graph.nodes
    for src, dst, data in graph.edges(data=True):
        dash = None
        if "dynamic_link" in data:
            if data["dynamic_link"]:
                dash = (4, 4)
        if not dash:
            canvas.create_line(
                nodes[src]["x"],
                nodes[src]["y"],
                nodes[dst]["x"],
                nodes[dst]["y"],
                fill="black",
            )
        else:
            canvas.create_line(
                nodes[src]["x"],
                nodes[src]["y"],
                nodes[dst]["x"],
                nodes[dst]["y"],
                fill="black",
                dash=dash,
            )


def draw_nodes():
    global graph
    global canvas
    global selected_node
    nodes = graph.nodes

    # update_status()

    # canvas.delete("all")

    # draw_links()

    for node, val in nodes.items():
        color = "orange"
        if val["type"] == "Switch":
            color = "blue"
        if node == selected_node:
            color = "green"
        if val["type"] == "Switch":
            box_size = 40
            canvas.create_rectangle(
                val["x"] - box_size / 2,
                val["y"] - box_size / 2,
                val["x"] + box_size / 2,
                val["y"] + box_size / 2,
                fill=color,
            )
            canvas.create_text(
                val["x"],
                val["y"] - box_size / 2 - 15,
                text=f'{val["name"]}',
                fill="black",
            )

        else:
            canvas.create_oval(
                val["x"] - 10, val["y"] - 10, val["x"] + 10, val["y"] + 10, fill=color
            )
            canvas.create_text(
                val["x"] - 15, val["y"] + 35, text=f'{val["name"]}', fill="black"
            )


def prop_changed(*args):
    print("Property changed")
    global graph
    global selected_node
    if prop_name.get() != "":
        graph.nodes[selected_node]["name"] = prop_name.get()
    if prop_nodeid.get() != "":
        new_nodeid = int(prop_nodeid.get())
        if new_nodeid != selected_node:
            if new_nodeid in graph.nodes:
                print(f"Node {new_nodeid} already exists")
                messagebox.showerror("Error", f"Node ID {new_nodeid} already exists")
                prop_nodeid.set(selected_node)
                return
            graph.add_node(new_nodeid)
            graph.nodes[new_nodeid].update(graph.nodes[selected_node])
            # add edges from old node to new node
            for src, dst in graph.edges:
                if dst == selected_node:
                    graph.add_edge(src, new_nodeid)
                if src == selected_node:
                    graph.add_edge(new_nodeid, dst)
            graph.remove_node(selected_node)
            selected_node = new_nodeid
        graph.nodes[selected_node]["name"] = prop_name.get()
    if prop_x.get() != "":
        graph.nodes[selected_node]["x"] = float(prop_x.get())
    if prop_y.get() != "":
        graph.nodes[selected_node]["y"] = float(prop_y.get())
    update_ui()


def add_node(x: float, y: float, node_type: str):
    global graph
    global next_node_num
    global selected_node

    graph.add_node(next_node_num)
    if node_type == "Switch":
        graph.nodes[next_node_num].update(
            {"x": x, "y": y, "type": node_type, "name": f"net_{next_node_num}"}
        )
    else:
        graph.nodes[next_node_num].update(
            {"x": x, "y": y, "type": node_type, "name": f"n{next_node_num}"}
        )
    print(f"Added node {next_node_num} at {x}, {y}")
    selected_node = next_node_num
    update_ui()
    # draw_properties()

    next_node_num += 1


def delete_node():
    global graph
    global selected_node
    global canvas
    # global status

    if selected_node == 0:
        # status.text = 'No node selected'
        print("No node selected")
        return
    graph.remove_node(selected_node)

    selected_node = 0
    update_ui()
    # draw_properties()

    # status.text = 'Node deleted'


btns = []


def toolbar(root):
    global nodevar
    global btns
    btn_bar = ttk.Frame(root)
    # frame.pack()
    btns = []
    btn_select = ttk.Button(btn_bar, text="Select")
    btn_select.pack(side=LEFT)

    btns.append(btn_select)
    btn_move = ttk.Button(btn_bar, text="Move")
    btn_move.pack(side=LEFT)
    btns.append(btn_move)

    btn_node = ttk.Button(btn_bar, text="Node")
    btn_node.pack(side=LEFT)
    btn_node.state(["disabled"])
    btns.append(btn_node)

    btn_link = ttk.Button(btn_bar, text="Link")
    btn_link.pack(side=LEFT)
    btns.append(btn_link)

    # for btn in btns:
    #     print(btn['text'])
    #     btn['command'] = lambda: write_slogan(btn['text'], btns)
    btn_select["command"] = lambda: toolbtn_click(btn_select, btns)
    btn_move["command"] = lambda: toolbtn_click(btn_move, btns)
    btn_node["command"] = lambda: toolbtn_click(btn_node, btns)
    btn_link["command"] = lambda: toolbtn_click(btn_link, btns)

    root.bind("<Control-Key-1>", lambda e: toolbtn_click(btn_select, btns))
    root.bind("<Control-Key-2>", lambda e: toolbtn_click(btn_move, btns))
    root.bind("<Control-Key-3>", lambda e: toolbtn_click(btn_node, btns))
    root.bind("<Control-Key-4>", lambda e: toolbtn_click(btn_link, btns))

    combo = ttk.Combobox(
        btn_bar,
        textvariable=nodevar,
    )
    combo["values"] = ("Host", "Switch")
    combo.current(0)
    combo.state(["readonly"])
    combo.pack(side=LEFT, padx=20)

    btn_setup = ttk.Button(
        btn_bar,
        text="Setup",
        command=lambda e=(canvas_w, canvas_h): dialog_setup(e[0], e[1]),
    )
    btn_setup.pack(side=RIGHT)

    return btn_bar


def node_at(x: float, y: float) -> int:
    global graph
    nodes = graph.nodes
    for node, val in nodes.items():
        size = 10
        if val["type"] == "Switch":
            size = 20
        if abs(val["x"] - x) < 10 and abs(val["y"] - y) < 10:
            return node
    return 0


def toolbtn_click(self, btns):
    print("clicked")
    global active_tool
    for btn in btns:
        btn.state(["!disabled"])
        if btn == self:
            btn.state(["disabled"])
    # self.state(["disabled"])
    active_tool = self["text"]
    # print("Tkinter is easy to use!")
    global nodevar
    # print(nodevar.get())


def canvas_click(event):
    event.widget.focus_set()
    lastx, lasty = canvas.canvasx(event.x), canvas.canvasy(event.y)
    # print("clicked at", lastx, lasty)
    if active_tool == "Node":
        add_node(lastx, lasty, nodevar.get())
    elif active_tool == "Select" or active_tool == "Move" or active_tool == "Link":
        global selected_node
        new_selected_node = node_at(lastx, lasty)
        if new_selected_node != 0:
            selected_node = new_selected_node
            update_ui()


def canvas_drag(event):
    global canvas
    global active_tool
    global selected_node
    global graph

    lastx, lasty = canvas.canvasx(event.x), canvas.canvasy(event.y)

    # print("dragged at", event.x, event.y)
    if active_tool == "Move":
        # node_to_move = node_at(event.x, event.y)
        if selected_node != 0:
            # selected_node = node_to_move
            graph.nodes[selected_node]["x"] = lastx
            graph.nodes[selected_node]["y"] = lasty
            update_ui()
    if active_tool == "Link":
        if selected_node != 0:
            update_ui()
            canvas.create_line(
                graph.nodes[selected_node]["x"],
                graph.nodes[selected_node]["y"],
                lastx,
                lasty,
                fill="black",
            )


def canvas_release(event):
    global graph
    global selected_node
    lastx, lasty = canvas.canvasx(event.x), canvas.canvasy(event.y)
    # print("released at", lastx, lasty)
    dst_node = node_at(lastx, lasty)
    if dst_node != 0 and dst_node != selected_node:
        if active_tool == "Link":
            default_link_props = {
                "bw": 0,
                "delay": 0.0,
                "jitter": 0.0,
                "loss": 0.0,
            }
            graph.add_edge(selected_node, dst_node, **default_link_props)
            selected_node = dst_node
    update_ui()


def on_menu_new_file():
    global graph
    global next_node_num
    global selected_node
    global current_filename
    global root

    graph.clear()
    next_node_num = 1
    selected_node = 0
    current_filename = ""
    root.title("NetEdit")

    update_ui()


def on_menu_open_file():
    print("Open file")
    global graph
    global current_filename
    global root
    global selected_node
    global next_node_num
    global active_tool
    global btns

    current_filename = filedialog.askopenfilename(
        defaultextension=".graphml",
        filetypes=[("GraphML files", "*.graphml"), ("All files", "*.*")],
    )
    if current_filename != None and current_filename != "":
        graph = nx.read_graphml(current_filename)
        root.title(f"NetEdit - {current_filename}")
        selected_node = 0
        active_tool = "Select"
        toolbtn_click(btns[0], btns)
        # get highest node number from graph.nodes
        next_node_num = sorted([int(n) for n in graph.nodes])[-1] + 1
        update_ui()


def on_menu_save_file():
    print("Save file")
    global graph
    global current_filename
    if current_filename == "":
        on_menu_save_as_file()
    else:
        nx.write_graphml(graph, current_filename)


def on_menu_save_as_file():
    print("Save as file")
    global graph
    global current_filename
    global root
    current_filename = filedialog.asksaveasfilename(
        defaultextension=".graphml",
        filetypes=[("GraphML files", "*.graphml"), ("All files", "*.*")],
    )
    if current_filename != None and current_filename != "":
        nx.write_graphml(graph, current_filename)
        root.title(f"NetEdit - {current_filename}")


def on_menu_about():
    print("About")
    messagebox.showinfo(
        "About", "NetEdit v0.1\n\n(c) 2022, Lars Baumgaertner\nAll rights reserved."
    )


root = Tk()
root.title("NetEdit")
root.option_add("*tearOff", FALSE)
menubar = Menu(root)
root["menu"] = menubar
menu_file = Menu(menubar)
menubar.add_cascade(menu=menu_file, label="File")
menu_file.add_command(label="New", command=on_menu_new_file)
menu_file.entryconfig("New", accelerator="Ctrl+N")
root.bind("<Control-n>", lambda e: on_menu_new_file())
menu_file.add_command(label="Open", command=on_menu_open_file)
menu_file.entryconfig("Open", accelerator="Ctrl+O")
root.bind("<Control-o>", lambda e: on_menu_open_file())
menu_file.add_command(label="Save", command=on_menu_save_file)
menu_file.entryconfig("Save", accelerator="Ctrl+S")
root.bind("<Control-s>", lambda e: on_menu_save_file())
menu_file.add_command(label="Save As", command=on_menu_save_as_file)
menu_file.entryconfig("Save As", accelerator="Ctrl+Shift+S")
root.bind("<Control-Shift-s>", lambda e: on_menu_save_as_file())

menu_file.add_separator()
menu_file.add_command(label="Quit", command=quit)
menu_file.entryconfig("Quit", accelerator="Ctrl+Q")
root.bind("<Control-q>", lambda e: quit())

# menu_edit = Menu(menubar)
# menubar.add_cascade(menu=menu_edit, label='Edit')

menu_help = Menu(menubar)
menubar.add_cascade(menu=menu_help, label="Help")
menu_help.add_command(label="About", command=on_menu_about)

nodevar = StringVar()


btn_bar = toolbar(root)

# p = ttk.Panedwindow(root, orient=HORIZONTAL)
# p.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky=(N, S, E, W))
p = root
canvas_frame = ttk.Frame(p, padding="3")
h = ttk.Scrollbar(canvas_frame, orient=HORIZONTAL)
h.grid(column=0, row=1, sticky=(W, E))
v = ttk.Scrollbar(canvas_frame, orient=VERTICAL)
v.grid(column=1, row=0, sticky=(N, S))
canvas_width = 800
canvas_height = 800
canvas = Canvas(
    canvas_frame,
    width=canvas_width,
    height=canvas_height,
    bg="white",
    scrollregion=(0, 0, canvas_w, canvas_h),
    yscrollcommand=v.set,
    xscrollcommand=h.set,
)
h["command"] = canvas.xview
v["command"] = canvas.yview
# canvas.pack(fill=BOTH, expand=True)
canvas.bind("<Button-1>", canvas_click)
canvas.bind("<B1-Motion>", canvas_drag)
canvas.bind("<ButtonRelease-1>", canvas_release)
canvas.grid(row=0, column=0, sticky=(N, S, E, W))
canvas_frame.columnconfigure(0, weight=1)
canvas_frame.rowconfigure(0, weight=1)


if background_image:
    img = ImageTk.PhotoImage(file=background_image)
    canvas.create_image(0, 0, image=img, anchor=NW)

properties = ttk.LabelFrame(p, text="Properties")
# properties.pack(side=RIGHT)
# p.add(canvas_frame)
# p.add(properties)


prop_name = add_label_entry(properties, "Name", 0)
prop_nodeid = add_label_entry(properties, "NODE_ID", 1)
prop_x = add_label_entry(properties, "X", 2)
prop_y = add_label_entry(properties, "Y", 3)
ttk.Separator(properties, orient=HORIZONTAL).grid(row=4, columnspan=2, sticky=(W, E))
ttk.Button(properties, text="Delete", command=delete_node).grid(row=5, columnspan=2)
ttk.Separator(properties, orient=HORIZONTAL).grid(row=4, columnspan=2, sticky=(W, E))
frame_links = ttk.LabelFrame(properties, text="Links")
frame_links.grid(row=6, columnspan=2, sticky=(W, E), padx=10, pady=10)


def delete_link(dst):
    global graph
    global selected_node
    print(f"Delete link from {selected_node} to {dst}")
    if graph.has_edge(selected_node, dst):
        graph.remove_edge(selected_node, dst)
    if graph.has_edge(dst, selected_node):
        graph.remove_edge(dst, selected_node)
    update_ui()


def show_dialog_link_properties(n1, n2, graph):
    win = dialog_link_properties(n1, n2, graph)
    root.wait_window(win)
    update_ui()


def draw_prop_links(frame):
    global graph
    global selected_node
    links = []
    for widget in frame.winfo_children():
        widget.destroy()

    if selected_node == 0:
        return
    for dst in graph.neighbors(selected_node):
        links.append(dst)
    for i, link in enumerate(sorted(links)):
        name = graph.nodes[link]["name"]
        ttk.Label(frame, text=f"-> {name}").grid(
            row=i, column=0, sticky=(W, E), padx=10, pady=10
        )
        ttk.Button(
            frame, text="Delete", command=lambda link=link: delete_link(link)
        ).grid(row=i, column=1, padx=10, pady=10)
        edge = (selected_node, link)

        ttk.Button(
            frame,
            text="Properties",
            command=lambda edge=edge: show_dialog_link_properties(
                edge[0], edge[1], graph
            ),
        ).grid(row=i, column=2, padx=10, pady=10)
        print(link)


draw_prop_links(frame_links)

# add status bar


statusframe = ttk.Frame(root)
statusBarVar = StringVar()
statusBarVar.set("Ready.")
status = ttk.Label(statusframe, textvariable=statusBarVar, relief=SUNKEN, anchor=W)
status.pack(fill=X, expand=True, padx=10, side=LEFT)

statusNodesVar = StringVar()
statusNodesVar.set("0")
status_nodes_label = ttk.Label(statusframe, text="Nodes:", anchor=W)
status_nodes_label.pack(padx=8, side=LEFT)
status_nodes = ttk.Label(
    statusframe, textvariable=statusNodesVar, relief=SUNKEN, anchor=E, width=10
)
status_nodes.pack(padx=10, side=LEFT)

statusLinksVar = StringVar()
statusLinksVar.set("0")
status_links_label = ttk.Label(statusframe, text="Links:", anchor=W)
status_links_label.pack(padx=8, side=LEFT)
status_links = ttk.Label(
    statusframe, textvariable=statusLinksVar, relief=SUNKEN, anchor=E, width=10
)
status_links.pack(padx=10, side=LEFT)

statusframe.grid(row=3, column=0, columnspan=4, sticky=(W, E, S), pady=10)

btn_bar.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=(N, E, W))

canvas_frame.grid(row=1, column=0, padx=10, pady=10, sticky=(N, S, E, W))
properties.grid(row=1, column=2, padx=10, pady=10, sticky=(N, S, E, W))

root.columnconfigure(0, weight=2)
root.rowconfigure(0, weight=0)
root.columnconfigure(1, weight=0)
root.rowconfigure(1, weight=2)


def main():
    global root
    global graph
    global current_filename
    global root
    global selected_node
    global next_node_num
    global active_tool
    global btns

    # check if sys.argv[1] is a file
    # if so, open it
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            current_filename = sys.argv[1]
            graph = nx.read_graphml(current_filename)
            root.title(f"NetEdit - {current_filename}")
            selected_node = 0
            active_tool = "Select"
            toolbtn_click(btns[0], btns)
            # get highest node number from graph.nodes
            next_node_num = int(sorted(list(graph.nodes))[-1]) + 1
            update_ui()
    else:
        graph = nx.Graph()
        current_filename = ""
        root.title("NetEdit")
        selected_node = 0
        next_node_num = 1
        update_ui()

    root.mainloop()


if __name__ == "__main__":
    main()
