import dash_bootstrap_components as dbc
from dash import html, dcc

import utils
from ..config import config


def settings_messages_component(settings):
    """
    builds the message settings
    @param settings: the settings defined in app.py
    """
    return [
        html.H6("Messages"),
        html.Div([
            dbc.Label('Interval (s)', html_for="msg_interval", className="form-label"),
            dcc.RangeSlider(min=config.messages.min_interval,
                            max=config.messages.max_interval,
                            step=config.messages.interval_step,
                            marks=utils.get_marks_dict(config.messages.min_interval,
                                                       config.messages.max_interval,
                                                       config.messages.interval_step),
                            value=[settings["MESSAGES"]["MIN_INTERVAL"],
                                   settings["MESSAGES"]["MAX_INTERVAL"]],
                            id="msg_interval")
        ], className="mt-2"),  # message interval
        html.Div([
            dbc.Label('Size', html_for="msg_size", className="form-label"),
            dcc.RangeSlider(
                min=config.messages.min_size,
                max=config.messages.max_size,
                step=config.messages.size_step,
                marks=utils.get_marks_dict(config.messages.min_size,
                                           config.messages.max_size,
                                           config.messages.size_step),
                value=[settings["MESSAGES"]["MIN_SIZE"], settings["MESSAGES"]["MAX_SIZE"]],
                id="msg_size")
        ], className="mt-2"),  # message size
        html.Div([
            dbc.Label('Time to live (s)', html_for="msg_ttl", className="form-label"),
            dcc.RangeSlider(
                min=config.messages.min_ttl,
                max=config.messages.max_ttl,
                step=config.messages.ttl_step,
                marks=utils.get_marks_dict(config.messages.min_ttl,
                                           config.messages.max_ttl,
                                           config.messages.ttl_step),
                value=[settings["MESSAGES"]["MIN_TTL"], settings["MESSAGES"]["MAX_TTL"]],
                id="msg_ttl"
            )
        ], className="mt-2")  # message ttl
    ]
