import inspect
import math
from typing import Tuple

import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, no_update, Input, Output, ctx, State
import dash_breakpoints

import pons
from ui import Visualization, DataManager, config
import utils

IGNORE_ROUTERS = ["Router"]

ROUTERS = {member: (cls(capacity=config.capacity) if "capacity" in inspect.getfullargspec(cls.__init__).args else cls())
           for (member, cls) in inspect.getmembers(pons.routing) if
           inspect.isclass(cls) and member not in IGNORE_ROUTERS}

settings = {
    "SIM_TIME": 3600,
    "WORLD_SIZE": (1000, 1000),  # fixed value
    "NUM_NODES": 10,
    "MIN_SPEED": 1.,
    "MAX_SPEED": 5.,
    "NET_RANGE": 50,
    "SIZEREF": 605. / 1000.,  # fixed value
    "FRAME_STEP": 1,
    "ROUTER": ROUTERS["EpidemicRouter"],
    "SHOW_NODE_IDS": True,
    "MESSAGES": {
        "MIN_INTERVAL": 30,
        "MAX_INTERVAL": 30,
        "MIN_SIZE": 0,
        "MAX_SIZE": 1028,
        "MIN_TTL": 3200,
        "MAX_TTL": 3600
    }
}

data_manager = DataManager(settings)
visualization = Visualization(data_manager, settings)
fig = visualization.get_figure()
app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO, dbc.icons.BOOTSTRAP])

# graph = dcc.Graph(figure=fig, id="plot", config={"displayModeBar": False}, className="mt-0 mb-0")

app.layout = html.Div([
    dbc.Row([
        dbc.Col(
            html.Div([
                dbc.Row([
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
                    ),
                ], className="mt-2"),
                dbc.Row([
                    dbc.Col(
                        html.Div([dcc.Graph(figure=fig, id="plot", config={"displayModeBar": False}, className="mt-0 mb-0 square-content", responsive=True)], className="square"),
                        width=9,
                    ),
                    dbc.Col(
                        html.Div([html.Div([html.Div([node], className="mt-2 mr-2"),
                                            dbc.Progress(value=0, className="mt-3 buffer w-100")],
                                           className="d-flex justify-content-between") for node in
                                  range(settings["NUM_NODES"])], id="buffer_div"),
                        width=3
                    )
                ]),
                dbc.Row([
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
                    dbc.Col(dcc.Slider(id="anim_slider",
                                       min=0,
                                       max=settings["SIM_TIME"],
                                       value=0,
                                       drag_value=0,
                                       step=10,
                                       className="w-100",
                                       marks={i: '{}'.format(i) for i in
                                              range(0, settings["SIM_TIME"], config.slider_marks_step)}),
                            width=10),
                ])
            ], className="mt-0 mb-2"), width=8),
        dbc.Col(html.Div([
            html.Div([
                html.Div([
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
                ]),
                html.Div([
                    dbc.Label('Number of nodes', html_for="num_nodes", className="form-label"),
                    dbc.Row([
                        dbc.Col(dcc.Input(id="num_nodes",
                                          type="range",
                                          min=config.min_num_of_nodes,
                                          max=config.max_num_of_nodes,
                                          step=config.num_of_nodes_step,
                                          value=settings["NUM_NODES"],
                                          className="form-control"), width=10),
                        dbc.Col(html.Span(settings["NUM_NODES"], id="num_nodes_display"), width=2)
                    ])
                ]),  # number of nodes input
                html.Div([
                    dbc.Label('Net range', html_for="net_range", className="form-label"),
                    dbc.Row([
                        dbc.Col(dcc.Input(id="net_range",
                                          type="range",
                                          min=config.min_net_range,
                                          max=config.max_net_range,
                                          step=config.net_range_step,
                                          value=settings["NET_RANGE"],
                                          className="form-control"), width=10),
                        dbc.Col(html.Span(settings["NET_RANGE"], id="net_range_display"), width=2)
                    ])
                ], className="mt-2"),  # net range input
                html.Div([
                    dbc.Label('Min. speed', html_for="min_speed", className="form-label"),
                    dbc.Row([
                        dbc.Col(dcc.Input(id="min_speed",
                                          type="range",
                                          min=config.min_speed,
                                          max=settings["MAX_SPEED"],
                                          step=config.speed_step,
                                          value=settings["MIN_SPEED"],
                                          className="form-control"), width=10),
                        dbc.Col(html.Span(settings["MIN_SPEED"], id="min_speed_display"), width=2)
                    ])
                ], className="mt-2"),  # min speed input
                html.Div([
                    dbc.Label('Max. speed', html_for="max_speed", className="form-label"),
                    dbc.Row([
                        dbc.Col(dcc.Input(id="max_speed",
                                          type="range",
                                          min=settings["MIN_SPEED"],
                                          max=config.max_speed,
                                          step=config.speed_step,
                                          value=settings["MAX_SPEED"],
                                          className="form-control"), width=10),
                        dbc.Col(html.Span(settings["MAX_SPEED"], id="max_speed_display"), width=2)
                    ])
                ], className="mt-2"),  # min speed input
                html.Div([
                    dbc.Label('Simulation time', html_for="sim_time", className="form-label"),
                    dbc.Row([
                        dbc.Col(dcc.Input(id="sim_time",
                                          type="range",
                                          min=config.min_sim_time,
                                          max=config.max_sim_time,
                                          step=config.sim_time_step,
                                          value=settings["SIM_TIME"],
                                          className="form-control"), width=10),
                        dbc.Col(html.Span(settings["SIM_TIME"], id="sim_time_display"), width=2)
                    ])
                ], className="mt-2"),  # sim time input
                html.Div([
                    dbc.Label('Router', html_for="router", className="form-label"),
                    dbc.Select(options=list(ROUTERS.keys()), value="EpidemicRouter", id="router")
                ], className="mt-2"),  # router input
                html.Hr(),
                html.H6("Messages"),
                html.Div([
                    dbc.Label('Interval (s)', html_for="msg_interval", className="form-label"),
                    dcc.RangeSlider(min=config.messages.min_interval,
                                    max=config.messages.max_interval,
                                    step=config.messages.interval_step,
                                    marks=utils.get_marks_dict(config.messages.min_interval,
                                                               config.messages.max_interval,
                                                               config.messages.interval_step),
                                    value=[settings["MESSAGES"]["MIN_INTERVAL"], settings["MESSAGES"]["MAX_INTERVAL"]],
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
                ], className="mt-2"),  # message ttl
            ], className="scrollable h-40"),
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
        ], className="mt-5 h-100", style={"margin-right": "30px"}), width=4)
    ], className="h-100"),
    dcc.Interval(id="anim_interval", interval=config.refresh_interval),
    html.Div("", id="size_helper", hidden=True),
    dash_breakpoints.WindowBreakpoints(id="breakpoints"),
], className="h-100 no-scroll")

app.clientside_callback(
    """
        async function getWidth (w, h) {
            var delay = ms => new Promise(res => setTimeout(res, ms));
            await delay(200);
            var plot = document.getElementsByClassName('bglayer')[0];
            if (plot == null) { return '0;0' };
            var rect = plot.getBoundingClientRect();
            return rect.width.toString() + ';' + rect.height.toString();;
        } 
    """,
    Output('size_helper', 'children', allow_duplicate=True),
    [Input("breakpoints", "width"), Input("breakpoints", "height")],
    prevent_initial_call=True
)

@app.callback(
    Output('size_helper', 'children', allow_duplicate=True),
    Input("size_helper", "children"),
    prevent_initial_call=True
)
def test(content):
    splitted = content.split(";")
    width = int(splitted[0])
    height = int(splitted[1])
    if width == 0:
        return no_update
    factor = (width + height) / 2.
    world_size_factor = (settings["WORLD_SIZE"][0] + settings["WORLD_SIZE"][1]) / 2
    settings["SIZEREF"] = factor / world_size_factor
    return factor

@app.callback(
    Output("checkbox_collapse", "is_open"),
    [Input("checkbox_collapse_button", "n_clicks")],
    [State("checkbox_collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [
        Output("plot", "figure", allow_duplicate=True),
        Output("anim_slider", "value", allow_duplicate=True),
        Output("event_div", "children", allow_duplicate=True),
        Output("buffer_div", "children", allow_duplicate=True)
    ],
    [Input("anim_slider", "value"), Input("anim_slider", "drag_value"), Input("anim_interval", "n_intervals")],
    prevent_initial_call=True
)
def animate(slider_value, drag_value, n_intervals):
    if "anim_slider.value" in ctx.triggered_prop_ids:
        if visualization.is_waiting():
            visualization.play()
        visualization.set_frame(int(slider_value))
        return _get_animation_outputs()
    if not visualization.is_playing():
        return _get_animation_outputs()
    if "anim_slider.drag_value" in ctx.triggered_prop_ids and slider_value != drag_value:
        visualization.wait()
        return no_update
    if "anim_interval.n_intervals" in ctx.triggered_prop_ids:
        if n_intervals is None:
            return no_update
        visualization.update_frame()
        return _get_animation_outputs()

    return no_update


def _get_animation_outputs() -> Tuple:
    frame = visualization.get_frame()
    return (
        visualization.get_figure(),
        frame,
        [html.Div([str(e)]) for e in data_manager.get_events(frame)],
        [html.Div([html.Div([key], className="mt-2 mr-2"),
                   dbc.Progress(value=value, className="mt-3 buffer w-100")],
                  className="d-flex justify-content-between") for key, value in
         data_manager.get_buffer(frame).items()]
    )


@app.callback(
    Output("playIcon", "className", allow_duplicate=True),
    Input("playButton", "n_clicks"),
    prevent_initial_call=True
)
def on_play_click(n_clicks):
    if visualization.is_playing():
        visualization.pause()
        return "bi bi-play"
    visualization.play()
    return "bi bi-pause"


@app.callback(
    Output("speed_slider", "value"),
    Input("speed_slider", "drag_value"),
    prevent_initial_call=True
)
def on_speed_drag(value):
    settings["FRAME_STEP"] = value
    visualization.set_settings(settings)
    return no_update

@app.callback(
    Output("plot", "figure"),
    Input("plot", "figure"),
    prevent_initial_call=True
)
def onplot(figure):
    return no_update


@app.callback(
    [
        Output("plot", "figure", allow_duplicate=True),
        Output("anim_slider", "value", allow_duplicate=True),
        Output("event_div", "children", allow_duplicate=True),
        Output("buffer_div", "children", allow_duplicate=True)
    ],
    Input("stepButton", "n_clicks"),
    prevent_initial_call=True
)
def on_step_click(n_clicks):
    frame = (visualization.get_frame() + settings["FRAME_STEP"]) % settings["SIM_TIME"]
    visualization.set_frame(frame)
    return (
        visualization.get_figure(),
        frame,
        [html.Div([str(e)]) for e in data_manager.get_events(frame)],
        [html.Div([html.Div([key], className="mt-2 mr-2"),
                   dbc.Progress(value=value, className="mt-3 buffer w-100")],
                  className="d-flex justify-content-between") for key, value in
         data_manager.get_buffer(frame).items()]
    )


@app.callback(
    Output("num_nodes_display", "children"),
    Input("num_nodes", "value"),
    prevent_initial_call=True
)
def on_num_nodes(value):
    return value


@app.callback(
    Output("net_range_display", "children"),
    Input("net_range", "value"),
    prevent_initial_call=True
)
def on_net_range(value):
    return value


@app.callback(
    [Output("min_speed", "max"), Output("max_speed_display", "children")],
    Input("max_speed", "value"),
    prevent_initial_call=True
)
def on_max_speed(value):
    return value, value


@app.callback(
    [Output("max_speed", "min"), Output("min_speed_display", "children")],
    Input("min_speed", "value"),
    prevent_initial_call=True
)
def on_min_speed(value):
    return value, value


@app.callback(
    Output("sim_time_display", "children"),
    Input("sim_time", "value"),
    prevent_initial_call=True
)
def on_sim_time(value):
    return value


@app.callback(
    [
        Output("plot", "figure", allow_duplicate=True),
        Output("playIcon", "className", allow_duplicate=True),
        Output("anim_slider", "value", allow_duplicate=True),
        Output("anim_slider", "max", allow_duplicate=True),
        Output("anim_slider", "marks"),
        Output("save_button_content", "children"),
        Output("anim_interval", "interval"),
    ],
    Input("saveButton", "n_clicks"),
    [
        State("num_nodes", "value"),
        State("net_range", "value"),
        State("min_speed", "value"),
        State("max_speed", "value"),
        State("sim_time", "value"),
        State("router", "value"),
        State("msg_interval", "value"),
        State("msg_size", "value"),
        State("msg_ttl", "value"),
    ],
    prevent_initial_call=True
)
def on_save(n_clicks, num_nodes, net_range, min_speed, max_speed, sim_time, router, msg_interval, msg_size, msg_ttl):
    visualization.pause()
    sim_time = int(sim_time)
    settings["NUM_NODES"] = int(num_nodes)
    settings["NET_RANGE"] = int(net_range)
    settings["MIN_SPEED"] = float(min_speed)
    settings["MAX_SPEED"] = float(max_speed)
    settings["SIM_TIME"] = sim_time
    settings["ROUTER_CLASS"] = ROUTERS[router]
    settings["MESSAGES"]["MIN_INTERVAL"] = msg_interval[0]
    settings["MESSAGES"]["MAX_INTERVAL"] = msg_interval[1]
    settings["MESSAGES"]["MIN_SIZE"] = msg_size[0]
    settings["MESSAGES"]["MAX_SIZE"] = msg_size[1]
    settings["MESSAGES"]["MIN_TTL"] = msg_ttl[0]
    settings["MESSAGES"]["MAX_TTL"] = msg_ttl[1]
    data_manager.update_settings(settings)
    visualization.set_settings(settings)
    visualization.on_data_update()
    visualization.set_frame(0)
    return (
        visualization.get_figure(),
        "bi bi-play-fill",
        0,
        sim_time, {i: '{}'.format(i) for i in range(0, sim_time, int(sim_time / 20))},
        "Save",
        config.refresh_interval
    )


@app.callback(
    [
        Output("num_nodes", "value", allow_duplicate=True),
        Output("net_range", "value", allow_duplicate=True),
        Output("min_speed", "value", allow_duplicate=True),
        Output("max_speed", "value", allow_duplicate=True)
    ],
    Input("resetButton", "n_clicks"),
    prevent_initial_call=True
)
def on_reset(n_clicks):
    return settings["NUM_NODES"], settings["NET_RANGE"], settings["MIN_SPEED"], settings["MAX_SPEED"],


@app.callback(
    Output("plot", "figure", allow_duplicate=True),
    Input("checkbox_input", "value"),
    prevent_initial_call=True
)
def on_checkbox_input(value):
    settings["SHOW_NODE_IDS"] = 1 in value
    return visualization.get_figure()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
