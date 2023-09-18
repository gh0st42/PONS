import random
from typing import Dict, Any, Tuple, List

import pandas as pd

import pons

RANDOM_SEED = 42

random.seed(RANDOM_SEED)


class DataManager:
    """handling everything regarding the data preparation for the visualization"""

    def __init__(self, settings: Dict[str, Any]):
        self._settings: Dict[str, Any] = settings
        self._moves: List[Tuple[float, int, int, int]] = []
        self._helper: Dict[float, Dict[int, Tuple[int, int]]] = {}
        self._data: Dict[float, Dict[str, List]] = {}
        self._events: Dict[float, Dict[str, List]] = {}
        self._events_list: List["pons.Event"] = []
        self._stores: Dict[float, Dict[int, List[pons.Message]]] = {}
        self._connections: Dict[float, List[pd.DataFrame]] = {}
        self._generate()

    def _generate_movement(self) -> List[Tuple[float, int, int, int]]:
        world_size = self._settings["WORLD_SIZE"]
        return pons.generate_randomwaypoint_movement(self._settings["SIM_TIME"],
                                                     self._settings["NUM_NODES"],
                                                     world_size[0],
                                                     world_size[1],
                                                     max_pause=60.0,
                                                     min_speed=self._settings["MIN_SPEED"],
                                                     max_speed=self._settings["MAX_SPEED"])

    def _simulate(self):
        """simulations as shown in sim.py"""
        self._moves = self._generate_movement()

        num_nodes = self._settings["NUM_NODES"]
        net = pons.NetworkSettings("WIFI_50m", range=self._settings["NET_RANGE"])

        nodes = pons.generate_nodes(
            num_nodes, net=[net], router=self._settings["ROUTER"])
        config = {"movement_logger": False, "peers_logger": False}

        msggenconfig = {
            "type": "single",
            "interval": (self._settings["MESSAGES"]["MIN_INTERVAL"], self._settings["MESSAGES"]["MAX_INTERVAL"]),
            "src": (0, num_nodes),
            "dst": (0, num_nodes),
            "size": (self._settings["MESSAGES"]["MIN_SIZE"], self._settings["MESSAGES"]["MAX_SIZE"]),
            "id": "M",
            "ttl": (self._settings["MESSAGES"]["MIN_TTL"], self._settings["MESSAGES"]["MAX_TTL"])
        }

        netsim = pons.NetSim(self._settings["SIM_TIME"], self._settings["WORLD_SIZE"], nodes, self._moves,
                             config=config, msggens=[msggenconfig])

        netsim.setup()
        netsim.run()
        self._events_list = sorted(netsim.event_manager.events, key=lambda e: e.time)

    def _add(self,
             data: Dict[float, Dict[str, List]],
             helper: Dict[float, Dict[int, Tuple[int, int]]],
             time: float,
             node: int,
             x: int,
             y: int):
        data[time]["node"].append(str(node))
        data[time]["x"].append(x)
        data[time]["y"].append(y)
        data[time]["stores"].append(f"<b>{node}</b><br>{'<br>'.join([msg.id for msg in self._stores[time][node]])}")
        helper[time][node] = (x, y)

    def _add_missing_data(self, data: Dict[float, Dict[str, List]], helper: Dict[float, Dict[int, Tuple[int, int]]]):
        for time in range(self._settings["SIM_TIME"]):
            time = float(time)
            if time not in data:
                data[time] = {"node": [], "x": [], "y": [], "stores": []}
                helper[time] = {}
            for node in range(self._settings["NUM_NODES"]):
                if node in helper[time]:
                    continue
                x, y = helper[time - 1][node]
                self._add(data, helper, time, node, x, y)

    def _generate_data(self):
        """generates movement data"""
        data = {}
        helper = {}
        for move in self._moves:
            time = move[0]
            node = move[1]
            x = move[2]
            y = move[3]
            if time not in data:
                data[time] = {"node": [], "x": [], "y": [], "stores": []}
                helper[time] = {}
            self._add(data, helper, time, node, x, y)
        self._add_missing_data(data, helper)
        self._data = data
        self._helper = helper

    def _add_event(self, target: Dict[float, Dict[str, List]], event: pons.Event):
        """adds event to event data"""
        time = event.time
        if time not in self._helper or event.from_node not in self._helper[time]:
            return
        target[time]["type"].append(event.type)
        from_x, from_y = self._helper[time][event.from_node]
        target[time]["from_x"].append(from_x)
        target[time]["from_y"].append(from_y)
        to_x, to_y = self._helper[time][event.node]
        target[time]["to_x"].append(to_x)
        target[time]["to_y"].append(to_y)

    def _generate_event_data(self):
        """generates event data"""
        data = {}
        for event in self._events_list:
            if event.time not in data:
                data[event.time] = {"type": [], "from_x": [], "from_y": [], "to_x": [], "to_y": []}
            self._add_event(data, event)
        self._events = data

    def _generate_connections(self):
        """generates connection data"""
        data = {}
        current_conns = set()
        # for each time
        for time in range(0, self._settings["SIM_TIME"]):
            data[time] = []
            # for every event that takes place at that time
            for event in [event for event in self._events_list if event.time == time]:
                # if event is CONNECTION_UP
                if event.type == pons.EventType.CONNECTION_UP:
                    # add connection to current_conns
                    current_conns.add(frozenset((event.node, event.from_node)))
                # else if event is CONNECTION_DOWN
                elif event.type == pons.EventType.CONNECTION_DOWN:
                    # remove event from current_conns
                    conn = frozenset((event.node, event.from_node))
                    if conn in current_conns:
                        current_conns.remove(conn)
            # for each connection
            for conn in current_conns:
                node1, node2 = tuple(conn)
                # extract coordinates and append to data
                from_x, from_y = self._helper[time][node1]
                to_x, to_y = self._helper[time][node2]
                data[time].append(pd.DataFrame.from_dict({
                    "x": [from_x, to_x],
                    "y": [from_y, to_y]
                }))
        self._connections = data

    def _generate_stores(self):
        """generates the store data"""
        # set stores for time=0 to empty sets
        stores = {0: {i: set() for i in range(0, self._settings["NUM_NODES"])}}
        # for each time starting with 1
        for time in range(1, self._settings["SIM_TIME"]):
            # copy the stores of time - 1
            stores[time] = {i: stores[time - 1][i].copy() for i in range(0, self._settings["NUM_NODES"])}
            # for each event
            for event in self._events_list:
                # that takes place at the time
                if time != event.time:
                    continue
                # if event is of types CREATED, RECEIVED or DELIVERED
                if event.type in [pons.EventType.CREATED, pons.EventType.RECEIVED, pons.EventType.DELIVERED]:
                    # add the message to the store
                    stores[time][event.node].add(event.message)
                # else if event is of type DROPPED
                elif event.type == pons.EventType.DROPPED:
                    if event.message in stores[time][event.node]:
                        # remove the message from the store
                        stores[time][event.node].remove(event.message)
        self._stores = stores

    def _generate(self):
        """generates all data"""
        self._simulate()
        self._generate_stores()
        self._generate_data()
        self._generate_event_data()
        self._generate_connections()

    @staticmethod
    def _to_dataframes(data: Dict[float, Dict[str, List]]) -> Dict[float, pd.DataFrame]:
        """converts dicts to dataframes"""
        dfs = {}
        for time in data:
            dfs[time] = pd.DataFrame.from_dict(data[time])
        return dfs

    def get_data(self) -> Dict[float, pd.DataFrame]:
        """gets the movement data"""
        return self._to_dataframes(self._data)

    def get_event_data(self, types) -> Dict[float, List[pd.DataFrame]]:
        """
        loads event data for given types (used for message relay visualization)
        @param types: list of event types
        @return: dict mapping time to event dataframe
        """
        data: Dict[float, Any] = {}
        for time in self._events:
            data[time] = []
            event = self._events[time]
            for i in range(0, len(event["from_x"])):
                if event["type"][i] in types:
                    data[time].append(pd.DataFrame.from_dict({
                        "x": [event["from_x"][i], event["to_x"][i]],
                        "y": [event["from_y"][i], event["to_y"][i]]
                    }))
        return data

    def get_buffer(self, time: float) -> Dict[int, float]:
        """
        gets the data for the buffer animation
        @param time: current time
        @return: dict mapping node to buffer fullness
        """
        capacity = self._settings["ROUTER"].capacity
        data = {}
        # for every node
        for i in range(0, self._settings["NUM_NODES"]):
            # get current stored messages
            messages = self._stores[time][i]
            # calculate total size
            size = sum([msg.size for msg in messages])
            # calculate fullness
            data[i] = (float(size) / float(capacity)) * 100.
        return data

    def get_connection_data(self):
        """gets the connection data between nodes"""
        return self._connections

    def get_events(self, until: float, exclude_types=None):
        """
        get events until given time with the possibility to exclude event types
        @param until: time until the events should be returned
        @param exclude_types: (optional) list of types to exclude
        @return: events as strings in order
        """
        if exclude_types is None:
            exclude_types = []
        return reversed([str(e) for e in self._events_list if e.time <= until if e.type not in exclude_types])

    def update_settings(self, settings: Dict[str, Any]):
        """
        updates settings
        @param settings: the settings dict from app.py
        """
        self._settings = settings
        self._generate()
