import dash_bootstrap_components as dbc
from dash import html, dcc

from ..config import config, ROUTERS


def settings_sim_component(settings):
    """
    builds the simulation settings
    @param settings: the settings defined in app.py
    """
    return [
        html.Div([
            dbc.Label('Number of nodes', html_for="num_nodes", className="form-label"),
            dbc.Row([
                dbc.Col(dcc.Input(id="num_nodes",
                                  type="range",
                                  min=config.min_num_of_nodes,
                                  max=config.max_num_of_nodes,
                                  step=config.num_of_nodes_step,
                                  value=settings["NUM_NODES"],
                                  className="form-control"), width=10),
                dbc.Col(html.Span(settings["NUM_NODES"], id="num_nodes_display"), width=2)
            ])
        ]),  # number of nodes input
        html.Div([
            dbc.Label('Net range', html_for="net_range", className="form-label"),
            dbc.Row([
                dbc.Col(dcc.Input(id="net_range",
                                  type="range",
                                  min=config.min_net_range,
                                  max=config.max_net_range,
                                  step=config.net_range_step,
                                  value=settings["NET_RANGE"],
                                  className="form-control"), width=10),
                dbc.Col(html.Span(settings["NET_RANGE"], id="net_range_display"), width=2)
            ])
        ], className="mt-2"),  # net range input
        html.Div([
            dbc.Label('Min. speed', html_for="min_speed", className="form-label"),
            dbc.Row([
                dbc.Col(dcc.Input(id="min_speed",
                                  type="range",
                                  min=config.min_speed,
                                  max=settings["MAX_SPEED"],
                                  step=config.speed_step,
                                  value=settings["MIN_SPEED"],
                                  className="form-control"), width=10),
                dbc.Col(html.Span(settings["MIN_SPEED"], id="min_speed_display"), width=2)
            ])
        ], className="mt-2"),  # min speed input
        html.Div([
            dbc.Label('Max. speed', html_for="max_speed", className="form-label"),
            dbc.Row([
                dbc.Col(dcc.Input(id="max_speed",
                                  type="range",
                                  min=settings["MIN_SPEED"],
                                  max=config.max_speed,
                                  step=config.speed_step,
                                  value=settings["MAX_SPEED"],
                                  className="form-control"), width=10),
                dbc.Col(html.Span(settings["MAX_SPEED"], id="max_speed_display"), width=2)
            ])
        ], className="mt-2"),  # min speed input
        html.Div([
            dbc.Label('Simulation time', html_for="sim_time", className="form-label"),
            dbc.Row([
                dbc.Col(dcc.Input(id="sim_time",
                                  type="range",
                                  min=config.min_sim_time,
                                  max=config.max_sim_time,
                                  step=config.sim_time_step,
                                  value=settings["SIM_TIME"],
                                  className="form-control"), width=10),
                dbc.Col(html.Span(settings["SIM_TIME"], id="sim_time_display"), width=2)
            ])
        ], className="mt-2"),  # sim time input
        html.Div([
            dbc.Label('Router', html_for="router", className="form-label"),
            dbc.Select(options=list(ROUTERS.keys()), value="EpidemicRouter", id="router")
        ], className="mt-2")  # router input
    ]
