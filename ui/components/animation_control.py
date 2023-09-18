import dash_bootstrap_components as dbc
from dash import html, dcc

from ..config import config


def animation_control_component(settings):
    """
    builds the animation slider and step forward buttons
    @param settings: the settings defined in app.py
    """
    return dbc.Row([
        dbc.Col(
            html.Div([
                dbc.Button(
                    html.I(id="playIcon", className="bi bi-play"),
                    id="playButton",
                    color="primary",
                    outline=True,
                    className="ml-2 control-button"
                ),
                dbc.Button(
                    html.I(id="stepIcon", className="bi bi-skip-end"),
                    id="stepButton",
                    color="primary",
                    outline=True,
                    className="ml-2 control-button"
                )
            ]),
            width=2
        ),
        dbc.Col(
            dcc.Slider(
                id="anim_slider",
                min=0,
                max=settings["SIM_TIME"],
                value=0,
                drag_value=0,
                step=10,
                className="w-100",
                marks={i: '{}'.format(i) for i in
                       range(0, settings["SIM_TIME"], config.slider_marks_step)}
            ),
            width=10),
    ])
