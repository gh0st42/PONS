from typing import Dict

import pandas as pd
import plotly.express as px


WORLD_SIZE = (1000, 1000)
SIZEREF = (586.) / (1000.)


def get_figure(dataframe: pd.DataFrame, settings: Dict):
    fig = px.scatter(dataframe,
                     x="x",
                     y="y",
                     animation_frame="time",
                     animation_group="node",
                     hover_name="node",
                     range_x=[0, WORLD_SIZE[0]],
                     range_y=[0, WORLD_SIZE[1]],
                     color_discrete_sequence=["rgba(0, 204, 0, 0.5)"])
    #set_speed(fig, settings)
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 30
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 5
    fig.update_layout(width=800, height=800)  # TODO scale this by x and y
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_traces(marker={"size": settings["NET_RANGE"] * SIZEREF})
    fig.update_geos(projection_type="equirectangular", visible=True, resolution=110)
    return fig


def update_net_range(fig, settings: Dict):
    fig.update_traces(marker={"size": settings["NET_RANGE"] * SIZEREF})


def set_speed(figure, settings: Dict):
    speed_factor = settings["SPEED_FACTOR"]
    print(figure.layout.updatemenus[0])
    figure.update_layout(width=800,
                         height=800,
                         updatemenus=[
                             {
                                 'buttons': [{'args': [None, {'frame': {'duration': 30 * speed_factor, 'redraw': False},
                                                              'mode': 'immediate', 'fromcurrent': True, 'transition':
                                                                  {'duration': 5 * speed_factor, 'easing': 'linear'}}],
                                              'label': '&#9654;',
                                              'method': 'animate'},
                                             {'args': [[None], {'frame': {'duration': 0, 'redraw': False},
                                                                'mode': 'immediate', 'fromcurrent': True, 'transition':
                                                                    {'duration': 0, 'easing': 'linear'}}],
                                              'label': '&#9724;',
                                              'method': 'animate'}],
                                 'direction': 'left',
                                 'pad': {'r': 10, 't': 70},
                                 'showactive': False,
                                 'type': 'buttons',
                                 'x': 0.1,
                                 'xanchor': 'right',
                                 'y': 0,
                                 'yanchor': 'top'
                             }
                         ])