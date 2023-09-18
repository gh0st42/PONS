import inspect
from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json, LetterCase

import pons


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class MessageConfig:
    """config class for messages"""
    min_interval: int
    max_interval: int
    interval_step: int
    min_size: int
    max_size: int
    size_step: int
    min_ttl: int
    max_ttl: int
    ttl_step: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Config:
    """config class"""
    min_sim_time: int
    max_sim_time: int
    sim_time_step: int
    slider_marks_step: int
    min_num_of_nodes: int
    max_num_of_nodes: int
    num_of_nodes_step: int
    min_net_range: int
    max_net_range: int
    net_range_step: int
    min_speed: float
    max_speed: float
    speed_step: float
    frame_step_options: List[int]
    refresh_interval: int
    capacity: int
    messages: MessageConfig


with open("config.json", "r") as file:
    config = Config.from_json(file.read())

IGNORE_ROUTERS = ["Router"]

ROUTERS = {
    member: (cls(capacity=config.capacity) if "capacity" in inspect.getfullargspec(cls.__init__).args else cls())
    for (member, cls) in inspect.getmembers(pons.routing) if
    inspect.isclass(cls) and member not in IGNORE_ROUTERS
}
