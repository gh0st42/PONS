import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, no_update, Input, Output, callback
from dash_bootstrap_components import Col, Row

from ui import get_figure, get_dataframe, set_speed


MAX_SPEED_FACTOR = 10.


class UI(Dash):
    def __init__(self):
        super().__init__(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._register_callbacks()
        self.settings = {
            "NUM_NODES": 10,
            "SPEED_FACTOR": 1.
        }
        df = get_dataframe(self.settings)
        self.fig = get_figure(df, self.settings)

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
                            html.Span('', id="num_nodes_display", style={'display': 'inline-block', 'margin-left': 20}),
                        ]),  # number of nodes input
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
            Output("num_nodes_display", "children"),
            Input("num_nodes", "value")
        )(self.on_num_nodes_for_display)
        self.callback(
            Output("plot", "figure"),
            Input("num_nodes", "value")
        )(self.on_num_nodes_for_plot)
        self.callback(
            Output("speed_factor_display", "children"),
            Input("speed_factor", "value")
        )(self.on_speed_factor)

    def on_speed_factor(self, factor):
        self.settings["SPEED_FACTOR"] = MAX_SPEED_FACTOR - float(factor)
        set_speed(self.fig, self.settings)
        return factor

    def on_num_nodes_for_display(self, num_nodes):
        return num_nodes

    def on_num_nodes_for_plot(self, num_nodes):
        if num_nodes == self.settings["NUM_NODES"]:
            return no_update
        self.settings["NUM_NODES"] = int(num_nodes)
        df = get_dataframe(self.settings)
        self.fig = get_figure(df, self.settings)
        return self.fig


a = UI()
