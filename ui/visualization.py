from enum import Enum
from typing import Dict, Any

import plotly.graph_objects as go

import pons
import ui


class VisualizationStatus(Enum):
    """visualization status enum"""
    PLAY = 0
    PAUSE = 1
    WAIT = 2


class Visualization:
    """class handling the visualization of the simulation"""

    def __init__(self, data_manager: "ui.DataManager", settings: Dict[str, Any]):
        self._data_manager: ui.DataManager = data_manager
        self.on_data_update()
        self._settings: Dict[str, Any] = settings
        self._frame: int = 0
        self._status: VisualizationStatus = VisualizationStatus.PAUSE
        self.fig = None

    def get_figure(self) -> go.Figure:
        """
        returns the figure for the current frame
        """
        dataframe = self._data[float(self._frame)]
        world_size = self._settings["WORLD_SIZE"]

        fig = go.Figure()

        # remove all margins
        fig.update_layout(autosize=True, margin={ "l": 0, "r": 0, "t": 0, "b": 0})
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        fig.update_xaxes(title="", range=[0, world_size[0]])
        # removes double 0
        fig.update_yaxes(title="", range=[0 + 61, world_size[1]])

        # show node ids of SHOW_NODE_IDS is true
        mode = "markers" + ("+text" if self._settings["SHOW_NODE_IDS"] else "")

        # core of nodes
        fig.add_trace(go.Scattergl(
            x=dataframe["x"],
            y=dataframe["y"],
            text=dataframe["node"],
            textposition="top center",
            marker={
                # seems to max out at like 30-40 for scattergl
                "size": 7,
                "color": "rgba(204, 102, 255, 255)",
            },
            line={"width": 0},
            showlegend=False,
            hoverinfo="text",
            hovertext=dataframe["stores"],
            mode=mode
        ))

        # radius of ndoes
        fig.add_trace(go.Scatter(
            x=dataframe["x"],
            y=dataframe["y"],
            marker={
                "size": self._settings["NET_RANGE"] * self._settings["SIZEREF"],
                "color": "rgba(0, 0, 0, 0)",
                "line": {
                    "color": "rgba(102, 153, 255, 255)",
                    "width": 2
                }
            },
            hoverinfo="skip",
            showlegend=False
        ))

        # connections
        if self._frame in self._connected_events:
            for df in self._connected_events[float(self._frame)]:
                fig.add_trace(go.Scattergl(
                    x=df["x"],
                    y=df["y"],
                    showlegend=False,
                    line={"color": "rgba(0, 102, 204, 255)"},
                    mode="lines"
                ))

        # events
        if self._frame in self._received_events:
            for df in self._received_events[float(self._frame)]:
                fig.add_trace(go.Scattergl(
                    x=df["x"],
                    y=df["y"],
                    showlegend=False,
                    line={"color": "rgba(78, 252, 3, 255)"},
                    mode="lines"
                ))
        self.fig = fig
        return fig

    def set_settings(self, settings: Dict):
        """updates the settings"""
        self._settings = settings

    def on_data_update(self):
        """handles data update"""
        self._data = self._data_manager.get_data()
        self._connected_events = self._data_manager.get_connection_data()
        self._received_events = self._data_manager.get_event_data([pons.EventType.RECEIVED])

    def set_frame(self, frame: int):
        """sets the frame"""
        if frame > self._settings["SIM_TIME"]:
            raise KeyError(f'{frame} is not in the simulation time {self._settings["SIM_TIME"]})')
        self._frame = frame

    def update_frame(self):
        """updates the frame using the frame step from settings"""
        self._frame = (self._frame + self._settings["FRAME_STEP"]) % (self._settings["SIM_TIME"])

    def get_frame(self) -> int:
        """gets the current frame"""
        return self._frame

    def is_playing(self) -> bool:
        """returns true if the visualization is playing"""
        return self._status == VisualizationStatus.PLAY

    def is_pausing(self) -> bool:
        """returns true if the visualization is pausing"""
        return self._status == VisualizationStatus.PAUSE

    def is_waiting(self) -> bool:
        """returns true if the visualization is waiting"""
        return self._status == VisualizationStatus.WAIT

    def play(self):
        """sets the visualization status to PLAY"""
        self._status = VisualizationStatus.PLAY

    def pause(self):
        """sets the visualization status to PAUSE"""
        self._status = VisualizationStatus.PAUSE

    def wait(self):
        """sets the visualization status to WAIT"""
        self._status = VisualizationStatus.WAIT
