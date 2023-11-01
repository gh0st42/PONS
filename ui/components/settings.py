import dash_bootstrap_components as dbc
from dash import html, dcc

from .settings_inputs import settings_inputs_component


def settings_component(settings):
    """
    builds the settings part of the app
    @param settings: the settings defined in app.py
    """
    return html.Div([
        settings_inputs_component(settings),
        html.Div([
            dbc.Button("Reset",
                       id="resetButton",
                       color="secondary",
                       className="w-100",
                       style={"margin-right": "10px"}),
            dbc.Button(dcc.Loading("Save", id="save_button_content", type="dot"),
                       id="saveButton",
                       color="primary",
                       className="w-100",
                       style={"margin-left": "10px"}),
        ], className="d-flex justify-content-between mt-3"),  # Buttons
        html.Div([
            html.Div([], id="event_div", className="event-display")
        ], className="mt-3")  # Event Display
    ], className="mt-5 h-100", style={"margin-right": "30px"})
