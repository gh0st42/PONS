# Import packages
import copy
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dash_table, dcc
import dash_bootstrap_components as dbc

import pons
import pons.routing as pr

# Settings
SIM_TIME = 3600
NET_RANGE = 100
NUM_NODES = 10
WORLD_SIZE = (1000, 1000)
RUNS = 2  # TODO 10
MSG_GEN_INTERVAL = (20, 40)
MSG_SIZE = (150, 512)

ROUTERS = [pr.EpidemicRouter(), pr.SprayAndWaitRouter(copies=7), pr.SprayAndWaitRouter(copies=7, binary=True),
           pr.DirectDeliveryRouter(), pr.FirstContactRouter()]

# Run Simulation
net_stats = []
routing_stats = []
for router in ROUTERS:
    print("router: %s" % router)
    for run in range(RUNS):
        random.seed(run)
        print("run", run + 1)

        moves = pons.generate_randomwaypoint_movement(SIM_TIME,
                                                      NUM_NODES,
                                                      WORLD_SIZE[0],
                                                      WORLD_SIZE[1],
                                                      min_speed=1.0,
                                                      max_speed=3.0,
                                                      max_pause=120.0)
        net = pons.NetworkSettings("WIFI", range=NET_RANGE)

        nodes = pons.generate_nodes(NUM_NODES, net=[net], router=copy.deepcopy(router))
        config = {"movement_logger": False, "peers_logger": False}

        msggenconfig = {"interval": MSG_GEN_INTERVAL, "src": (0, NUM_NODES), "dst": (0, NUM_NODES), "size": MSG_SIZE,
                        "id": "M"}

        netsim = pons.NetSim(SIM_TIME, WORLD_SIZE, nodes, moves, config=config, msggens=[msggenconfig])

        netsim.setup()

        netsim.run()

        ns = copy.deepcopy(netsim.net_stats)
        ns['router'] = "" + str(router)
        net_stats.append(ns)
        rs = copy.deepcopy(netsim.routing_stats)
        rs['router'] = "" + str(router)
        routing_stats.append(rs)

df_routing = pd.DataFrame.from_dict(routing_stats, orient='columns')


def get_figure(attribute: str):
    fig = go.Figure(layout={"template": "plotly_dark",
                            "modebar": {"remove": ["zoom", "pan", "zoomin", "zoomout", "autoscale", "resetscale"]},
                            'xaxis': {'title': 'Routing Protocol',
                                      'visible': True,
                                      'showticklabels': True},
                            'yaxis': {'title': attribute,
                                      'visible': True,
                                      'showticklabels': True}
                            })
    for router in ROUTERS:
        name = str(router)
        fig.add_trace(go.Violin(x=df_routing["router"][df_routing["router"] == name],
                                y=df_routing[attribute][df_routing["router"] == name],
                                name=name,
                                box_visible=True,
                                meanline_visible=True, hoverinfo="skip", showlegend=False))

    return fig


ATTRIBUTES = ["delivery_prob", "latency_avg", "hops_avg", "overhead_ratio"]
figures = [get_figure(attribute) for attribute in ATTRIBUTES]
elements = [dbc.Col(dcc.Graph(figure=fig), width=6) for fig in figures]

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

# App layout
app.layout = html.Div([
    # html.Div(children='My First App with Data'),
    # dash_table.DataTable(data=net_stats, page_size=10),
    # dash_table.DataTable(data=routing_stats, page_size=10),
    dbc.Row(elements)
], className="bg-dark")

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
