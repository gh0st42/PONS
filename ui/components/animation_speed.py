import dash_bootstrap_components as dbc
from dash import html, dcc


def animation_speed_component():
    """
    builds the speed control for the animation
    """
    return dbc.Row([
        dbc.Col(
            html.Div(["Animation speed"], className="ml-2"),
            width=2
        ),
        dbc.Col(
            dcc.Slider(id="speed_slider",
                       min=1,
                       max=50,
                       step=None,
                       marks={1: "1", 2: "2", 5: "5", 10: "10", 20: "20", 30: "30", 40: "40", 50: "50"},
                       className="w-75"),
            width=10
        )
    ], className="mt-2")
