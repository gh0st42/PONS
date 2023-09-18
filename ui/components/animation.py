from dash import html

from .animation_control import animation_control_component
from .animation_graph import animation_graph_component
from .animation_speed import animation_speed_component


def animation_component(fig, settings):
    """
    builds all parts regarding animation (graphs, slider, speed, etc.)
    @param fig: the plotly figure
    @param settings: the settings defined in app.py
    """
    return html.Div([
        animation_speed_component(),
        animation_graph_component(fig, settings),
        animation_control_component(settings)
    ], className="mt-0 mb-2")
