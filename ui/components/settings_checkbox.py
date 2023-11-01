import dash_bootstrap_components as dbc
from dash import html


def settings_checkbox_component():
    """
    builds the checkbox settings
    """
    return html.Div([
        dbc.Button(
            html.I(className="bi bi-caret-down-fill"),
            id="checkbox_collapse_button",
            className="mb-3 control-button",
            color="primary",
            n_clicks=0,
        ),
        dbc.Collapse(
            dbc.Card(dbc.CardBody(
                dbc.Checklist(
                    options=[
                        {"label": "Show node ids", "value": 1},
                    ],
                    value=[1],
                    id="checkbox_input",
                ),
            )),
            id="checkbox_collapse",
            is_open=False,
        ),
    ])
