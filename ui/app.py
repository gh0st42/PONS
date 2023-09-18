from typing import Tuple

import dash_bootstrap_components as dbc
from dash import Dash, html, no_update, Input, Output, ctx, State

from ui import Visualization, DataManager, layout_component, config, ROUTERS

settings = {
    "SIM_TIME": 3600,
    "WORLD_SIZE": (1000, 1000),  # fixed value
    "NUM_NODES": 10,
    "MIN_SPEED": 1.,
    "MAX_SPEED": 5.,
    "NET_RANGE": 50,
    "SIZEREF": 605. / 1000.,
    "FRAME_STEP": 1,
    "ROUTER": ROUTERS["EpidemicRouter"],
    "ROUTER_NAME": "EpidemicRouter",
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

app.layout = layout_component(fig, settings)

# region Callbacks

# js code getting width and height of plot
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
    Output("checkbox_collapse", "is_open"),
    [Input("checkbox_collapse_button", "n_clicks")],
    [State("checkbox_collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    """
    toggling the checkbox collapse
    @param n: n_clicks of checkbox_collapse_button
    @param is_open: state of checkbox_collapse is_open property
    @return: toggled value for is_open
    """
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
    [
        Input("anim_slider", "value"),
        Input("anim_slider", "drag_value"),
        Input("anim_interval", "n_intervals")
    ],
    prevent_initial_call=True
)
def animate(slider_value, drag_value, n_intervals):
    """
    handles all animations
    @param slider_value: value of the animation slider
    @param drag_value: drag value of the animation slider
    @param n_intervals: current animation interval value
    @return: tuple consisting of the plot figure,
    the new slider value, the event_div content and the buffer_div content
    """
    # if slider value has been triggered
    if "anim_slider.value" in ctx.triggered_prop_ids:
        # if visualization is currently waiting because of drag_value
        if visualization.is_waiting():
            # start to play
            visualization.play()
        # set the visualization frame to the slider value
        visualization.set_frame(int(slider_value))
        return _get_animation_outputs()
    # else if visualization is currently not playing, do not change anything
    if not visualization.is_playing():
        return _get_animation_outputs()
    # else if drag value is triggered and it differs from the slider value
    if "anim_slider.drag_value" in ctx.triggered_prop_ids and slider_value != drag_value:
        # wait and do not change anything
        visualization.wait()
        return no_update
    # if the interval value has changed
    if "anim_interval.n_intervals" in ctx.triggered_prop_ids:
        if n_intervals is None:
            return no_update
        # update the frame
        visualization.update_frame()
        return _get_animation_outputs()

    return no_update


def _get_animation_outputs() -> Tuple:
    """
    returns the animation outputs as a tuple
    """
    frame = visualization.get_frame()
    return (
        # plot figure
        visualization.get_figure(),
        # current frame
        frame,
        # event_div content
        [html.Div([str(e)]) for e in data_manager.get_events(frame)],
        # buffer_div content
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
    """
    handling the play click
    @param n_clicks: n_clicks of playButton
    @return: new playIcon class
    """
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
    """
    handling the speed slider
    @param value: the drag_value of the speed slider
    @return: the slider value of the speed slider
    """
    settings["FRAME_STEP"] = value
    visualization.set_settings(settings)
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
    """
    handles a click on the step button
    @param n_clicks: n_clicks of the stepButton
    @return: tuple consisting of the plot figure,
    the new slider value, the event_div content and the buffer_div content
    """
    frame = (visualization.get_frame() + settings["FRAME_STEP"]) % settings["SIM_TIME"]
    visualization.set_frame(frame)
    return _get_animation_outputs()


@app.callback(
    Output("num_nodes_display", "children"),
    Input("num_nodes", "value"),
    prevent_initial_call=True
)
def on_num_nodes(value):
    """
    forwards input change of num_nodes slider to the display
    @param value: the slider value of num_nodes
    @return: the value for the display
    """
    return value


@app.callback(
    Output("net_range_display", "children"),
    Input("net_range", "value"),
    prevent_initial_call=True
)
def on_net_range(value):
    """
    forwards input change of net_range slider to the display
    @param value: the slider value of net_range
    @return: the value for the display
    """
    return value


@app.callback(
    [Output("min_speed", "max"), Output("max_speed_display", "children")],
    Input("max_speed", "value"),
    prevent_initial_call=True
)
def on_max_speed(value):
    """
    forwards input change of max_speed slider to the display and the max of min_speed
    @param value: the slider value of max_speed
    @return: a tuple consisting of the value for the display and the max value for min_speed
    """
    return value, value


@app.callback(
    [Output("max_speed", "min"), Output("min_speed_display", "children")],
    Input("min_speed", "value"),
    prevent_initial_call=True
)
def on_min_speed(value):
    """
    forwards input change of min_speed slider to the display and the min of max_speed
    @param value: the slider value of min_speed
    @return: a tuple consisting of the value for the display and the min value for max_speed
    """
    return value, value


@app.callback(
    Output("sim_time_display", "children"),
    Input("sim_time", "value"),
    prevent_initial_call=True
)
def on_sim_time(value):
    """
    forwards input change of sim_time slider to the display
    @param value: the slider value of sim_time
    @return: the value for the display
    """
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
    """
    saves changes to settings
    @param n_clicks: n_clicks of the saveButton
    @param num_nodes: state of num_nodes slider
    @param net_range: state of net_range slider
    @param min_speed: state of min_speed slider
    @param max_speed: state of max_speed slider
    @param sim_time: state of sim_time slider
    @param router: state of router dropdown
    @param msg_interval: state of msg_interval
    @param msg_size: state of msg_size
    @param msg_ttl: state of msg_ttl
    @return: a tuple consisting of the plot figure, the play icon class,
    the value of the animation slider, the max of the animation slider,
    the content of the save button, the animation interval
    """
    # pause the visualization
    visualization.pause()
    sim_time = int(sim_time)
    # update the settings
    settings["NUM_NODES"] = int(num_nodes)
    settings["NET_RANGE"] = int(net_range)
    settings["MIN_SPEED"] = float(min_speed)
    settings["MAX_SPEED"] = float(max_speed)
    settings["SIM_TIME"] = sim_time
    settings["ROUTER"] = ROUTERS[router]
    settings["ROUTER_NAME"] = router
    settings["MESSAGES"]["MIN_INTERVAL"] = msg_interval[0]
    settings["MESSAGES"]["MAX_INTERVAL"] = msg_interval[1]
    settings["MESSAGES"]["MIN_SIZE"] = msg_size[0]
    settings["MESSAGES"]["MAX_SIZE"] = msg_size[1]
    settings["MESSAGES"]["MIN_TTL"] = msg_ttl[0]
    settings["MESSAGES"]["MAX_TTL"] = msg_ttl[1]
    # forward the settings to all channels
    data_manager.update_settings(settings)
    visualization.set_settings(settings)
    # let the visualization know, that data has changed
    visualization.on_data_update()
    # start animation from start
    visualization.set_frame(0)
    return (
        # figure
        visualization.get_figure(),
        # play icon
        "bi bi-play-fill",
        # animation slider value
        0,
        # animation slider max
        sim_time, {i: '{}'.format(i) for i in range(0, sim_time, int(sim_time / 20))},
        # save button content
        "Save",
        # animation interval
        config.refresh_interval
    )


@app.callback(
    [
        Output("num_nodes", "value", allow_duplicate=True),
        Output("net_range", "value", allow_duplicate=True),
        Output("min_speed", "value", allow_duplicate=True),
        Output("max_speed", "value", allow_duplicate=True),
        Output("sim_time", "value", allow_duplicate=True),
        Output("router", "value", allow_duplicate=True),
        Output("msg_interval", "value", allow_duplicate=True),
        Output("msg_size", "value", allow_duplicate=True),
        Output("msg_ttl", "value", allow_duplicate=True),
    ],
    Input("resetButton", "n_clicks"),
    prevent_initial_call=True
)
def on_reset(n_clicks):
    """
    resets the inputs
    @param n_clicks: n_clicks of resetButton
    @return: tuple consisting of num_nodes, net_range, min_speed, max_speed,
    sim_time, router, msg_interval, msg_size, msg_ttl
    """
    return (
        settings["NUM_NODES"],
        settings["NET_RANGE"],
        settings["MIN_SPEED"],
        settings["MAX_SPEED"],
        settings["SIM_TIME"],
        settings["ROUTER_NAME"],
        [settings["MESSAGES"]["MIN_INTERVAL"], settings["MESSAGES"]["MAX_INTERVAL"]],
        [settings["MESSAGES"]["MIN_SIZE"], settings["MESSAGES"]["MAX_SIZE"]],
        [settings["MESSAGES"]["MIN_TTL"], settings["MESSAGES"]["MAX_TTL"]],
    )


@app.callback(
    Output("plot", "figure", allow_duplicate=True),
    Input("checkbox_input", "value"),
    prevent_initial_call=True
)
def on_checkbox_input(value):
    """
    shows node ids based on checkbox value
    @param value: the checkbox value
    @return: the plot figure
    """
    settings["SHOW_NODE_IDS"] = 1 in value
    return visualization.get_figure()


# endregion

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
