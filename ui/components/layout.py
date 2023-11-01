import dash_bootstrap_components as dbc
import dash_breakpoints
from dash import html, dcc

from .animation import animation_component
from .settings import settings_component
from ..config import config


def layout_component(fig, settings):
    """
    builds the apps layout
    @param fig: the plotly figure
    @param settings: the settings defined in app.py
    """
    return html.Div([
        dbc.Row([
            dbc.Col(
                animation_component(fig, settings),
                width=8
            ),
            dbc.Col(
                settings_component(settings),
                width=4
            )
        ], className="h-100"),
        dcc.Interval(id="anim_interval", interval=config.refresh_interval),
        html.Div("", id="size_helper", hidden=True),
        dash_breakpoints.WindowBreakpoints(id="breakpoints"),
    ], className="h-100 no-scroll")
