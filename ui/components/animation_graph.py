import dash_bootstrap_components as dbc
from dash import html, dcc


def animation_graph_component(fig, settings):
    """
    builds the graphs for the animation.
    @param fig: the plotly figure
    @param settings: the settings defined in app.py
    """
    return dbc.Row([
        dbc.Col(
            html.Div([dcc.Graph(figure=fig,
                                id="plot",
                                config={"displayModeBar": False},
                                className="mt-0 mb-0 square-content",
                                responsive=True)], className="square"),
            width=9,
        ),
        dbc.Col(
            html.Div([html.Div([html.Div([node], className="mt-2 mr-2"),
                                dbc.Progress(value=0, className="mt-3 buffer w-100")],
                               className="d-flex justify-content-between") for node in
                      range(settings["NUM_NODES"])], id="buffer_div"),
            width=3
        )
    ])
