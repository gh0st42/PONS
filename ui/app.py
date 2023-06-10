import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, no_update, Input, Output
from dash_bootstrap_components import Col, Row

from ui import get_figure, get_dataframe, set_speed, update_net_range

MAX_SPEED_FACTOR = 10.
SIZEREF = (586.) / (1000.)


class App(Dash):
    def __init__(self):
        super().__init__(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._register_callbacks()
        self.settings = {
            "NUM_NODES": 10,
            "SPEED_FACTOR": 1.,
            "NET_RANGE": 50
        }
        self.df = get_dataframe(self.settings)
        self.fig = get_figure(self.df, self.settings)

        self.layout = html.Div([
            # dcc.Graph(figure=fig),
            Row([
                Col(html.Center(
                    dcc.Loading(id="loading", children=[
                        dcc.Graph(id="plot", figure=self.fig)],
                                type="default")), width=8),
                Col(
                    html.Div([
                        html.Div([
                            html.Span('Number of nodes', style={'display': 'inline-block', 'margin-right': 20}),
                            dcc.Input(id="num_nodes",
                                      type="range",
                                      min=1,
                                      max=10,
                                      step=1,
                                      value=self.settings["NUM_NODES"],
                                      debounce=True,
                                      style={"display": "inline-block"}),
                            html.Span(self.settings["NUM_NODES"], id="num_nodes_display", style={'display': 'inline-block', 'margin-left': 20}),
                        ]),  # number of nodes input
                        html.Div([
                            html.Span('Net range', style={'display': 'inline-block', 'margin-right': 20}),
                            dcc.Input(id="net_range",
                                      type="range",
                                      min=20,
                                      max=150,
                                      step=5,
                                      value=self.settings["NET_RANGE"],
                                      debounce=True,
                                      style={"display": "inline-block"}),
                            html.Span(self.settings["NET_RANGE"], id="net_range_display", style={'display': 'inline-block', 'margin-left': 20}),
                        ]),  # net range input
                        html.Div([
                            html.Span('Speed', style={'display': 'inline-block', 'margin-right': 20}),
                            dcc.Input(id="speed_factor",
                                      type="range",
                                      min=0.05,
                                      max=10,
                                      step=0.05,
                                      value=self.settings["SPEED_FACTOR"],
                                      debounce=True,
                                      style={"display": "inline-block"}),
                            html.Span('',
                                      id="speed_factor_display",
                                      style={'display': 'inline-block', 'margin-left': 20}),
                        ], style={ "visibility": "hidden"}),  # speed factor input
                    ], className="mt-5"),
                    width=4),
                # dbc.Col(dcc.Input(type="range"), width=4)
            ]),
        ])

        self.run(debug=True)

    def _register_callbacks(self):
        self.callback(
            [Output("num_nodes_display", "children"), Output("plot", "figure", allow_duplicate=True)],
            Input("num_nodes", "value"),
            prevent_initial_call=True
        )(self.on_num_nodes)
        self.callback(
            Output("speed_factor_display", "children"),
            Input("speed_factor", "value"),
            prevent_initial_call=True
        )(self.on_speed_factor)
        self.callback(
            [Output("net_range_display", "children"), Output("plot", "figure", allow_duplicate=True)],
            Input("net_range", "value"),
            prevent_initial_call=True
        )(self.on_net_range)

    def on_speed_factor(self, factor):
        self.settings["SPEED_FACTOR"] = MAX_SPEED_FACTOR - float(factor)
        set_speed(self.fig, self.settings)
        return factor

    def on_num_nodes(self, num_nodes):
        num_nodes = int(num_nodes)
        if num_nodes == self.settings["NUM_NODES"]:
            return no_update
        self.settings["NUM_NODES"] = num_nodes
        self.df = get_dataframe(self.settings)
        self.fig = get_figure(self.df, self.settings)
        return num_nodes, self.fig

    def on_net_range(self, net_range):
        net_range = int(net_range)
        if net_range == self.settings["NET_RANGE"]:
            return no_update
        self.settings["NET_RANGE"] = net_range
        update_net_range(self.fig, self.settings)
        return net_range, self.fig


app = App()
