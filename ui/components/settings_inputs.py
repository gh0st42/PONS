from dash import html

from .settings_checkbox import settings_checkbox_component
from .settings_messages import settings_messages_component
from .settings_sim import settings_sim_component


def settings_inputs_component(settings):
    """
    builds the settings inputs
    @param settings: the settings defined in app.py
    """
    return html.Div(
        [settings_checkbox_component()] +
        settings_sim_component(settings) +
        [html.Hr()] +
        settings_messages_component(settings),
        className="scrollable h-40"
    )
