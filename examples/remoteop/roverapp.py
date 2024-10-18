import random
import sys
import pathlib
import math
from enum import Enum

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
print(SCRIPT_DIR)
try:
    import pons
except ImportError:
    print(SCRIPT_DIR.parent.parent.resolve())
    sys.path.append(str(SCRIPT_DIR.parent.parent.resolve()))
    import pons
SCRIPT_DIR = str(SCRIPT_DIR)

from pons.apps.app import App
from pons.event_log import event_log

# Supported rover commands:
# - forward: move forward at a given speed for a given time
# - turn: turn to a given angle
# - cancel: cancel the current movement
# - clear: clear the command queue
# - sleep: sleep for a given time


class RoverState(Enum):
    IDLE = 0
    MOVING = 1
    TURNING = 2
    SLEEPING = 3

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class Rover:
    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        netsim: pons.NetSim,
        direction: float = 0,
        battery: float = 100,
        max_speed: float = 1,
        turn_speed: float = 1,
        cmds: list = [],
    ):
        self.name = name
        self.x = x
        self.y = y
        self.direction = direction
        self.battery = battery
        self.speed = 0
        self.max_speed = max_speed
        self.turn_speed = turn_speed
        self.v_time = 0
        self.target_angle = self.direction
        self.cmds = cmds
        self.netsim = netsim
        self.my_id = None
        self.state = RoverState.IDLE

    def __str__(self):
        return "Rover (%s / %s | %s ) [%f, %f]" % (
            self.name,
            self.my_id,
            self.state,
            self.x,
            self.y,
        )

    def __repr__(self):
        return str(self)

    def log(self, msg):
        print("[ %f ] [%s] ROVER: %s" % (self.netsim.env.now, self.name, msg))

    def start(self, netsim: pons.NetSim, my_id: int):
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        self.netsim.env.process(self.battery_drainer())
        self.netsim.env.process(self.run())

    def battery_drainer(self):
        while True:
            if self.battery > 0:
                self.battery -= 0.1
            yield self.netsim.env.timeout(6)

    def forward(self, speed: float, duration: float):
        self.speed = min(speed, self.max_speed)
        self.v_time = duration

    def turn(self, angle: float):
        self.target_angle = angle
        self.target_angle %= 360

    def update_position(self, time: float = 1.0):
        if self.v_time > 0:
            self.x += self.speed * time * math.cos(math.radians(self.direction))
            self.y += self.speed * time * math.sin(math.radians(self.direction))
            self.v_time -= time
        else:
            self.speed = 0
            self.state = RoverState.IDLE

    def update_direction(self, time: float = 1.0):
        if self.direction != self.target_angle:
            diff = self.target_angle - self.direction
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            if diff > 0:
                self.direction += self.turn_speed * time
            else:
                self.direction -= self.turn_speed * time
            self.direction %= 360
        else:
            self.state = RoverState.IDLE

    def process_commands(self):
        if len(self.cmds) > 0:
            cmd = self.cmds[0]
            self.log("processing new command: %s" % cmd)
            if cmd[0] == "forward":
                self.forward(float(cmd[1]), float(cmd[2]))
                self.state = RoverState.MOVING
            elif cmd[0] == "turn":
                self.turn(float(cmd[1]))
                self.state = RoverState.TURNING
            self.cmds = self.cmds[1:]
        else:
            return
            self.log("no commands to process")

    def add_command(self, cmd):
        if cmd[0] == "cancel":
            self.target_angle = self.direction
            self.v_time = 0
            self.state = RoverState.IDLE
            self.log("canceled current movement")
        elif cmd[0] == "clear":
            self.cmds = []
            self.log("cleared command queue")
        else:
            self.cmds.append(cmd)

    def run(self):
        STEP_TIME = 1.0
        while True:
            if self.netsim.env.now % 20 == 0:
                self.log(
                    "position: [%f, %f], direction: %f, battery: %.01f, state: %s"
                    % (self.x, self.y, self.direction, self.battery, self.state)
                )
            if self.battery <= 0:
                self.log("battery depleted")
                yield self.netsim.env.timeout(10)
                continue

            if self.state == RoverState.IDLE:
                self.process_commands()

            if self.state == RoverState.MOVING:
                self.update_position(STEP_TIME)
                self.battery -= 0.2
            elif self.state == RoverState.TURNING:
                self.update_direction(STEP_TIME)
                self.battery -= 0.1
            elif self.state == RoverState.IDLE:
                self.process_commands()

            yield self.netsim.env.timeout(STEP_TIME)

    def get_status(self):
        return {
            "position": [self.x, self.y],
            "direction": self.direction,
            "battery": self.battery,
            "speed": self.speed,
            "state": self.state,
            "cmdbuflen": len(self.cmds),
        }


class RoverApp(App):
    def __init__(
        self,
        dst: int,
        service: int = 7,
        dst_service: int = 7,
        interval: float = 30.0,
        ttl: int = 3600,
        rnd_start: bool = False,
    ):
        super().__init__(service)
        self.msgs_sent = 0
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}
        self.interval = interval
        self.ttl = ttl
        self.dst = dst
        self.dst_service = dst_service
        self.rnd_start = rnd_start

    def __str__(self):
        return "RoverApp (%d, %d)" % (self.my_id, self.service)

    def log(self, msg):
        print(
            "[ %f ] [%s.%d] APP: %s"
            % (self.netsim.env.now, self.my_id, self.service, msg)
        )

    def start(self, netsim: pons.NetSim, my_id: int):
        self.rover = Rover("rover1", x=50, y=50, direction=0, netsim=netsim)
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        self.rover.start(netsim, my_id)
        self.netsim.env.process(self.run())

    def on_msg_received(self, msg: pons.Message):
        if msg.unique_id().startswith("TC"):
            self.log(
                "Telecommand received: %s | %s" % (msg.id, msg.content.decode("utf-8"))
            )
            self.msgs_received += 1
            content = msg.content.decode("utf-8").split(" ")
            self.rover.add_command(content)

    def run(self):
        if self.interval > 0:
            if self.rnd_start:
                delay = random.random() * self.interval
                yield self.netsim.env.timeout(delay)
            while True:
                content = self.rover.get_status()

                tm_hk_msg = pons.Message(
                    "TM-HK-%d" % self.msgs_sent,
                    self.my_id,
                    self.dst,
                    sys.getsizeof(content),
                    self.netsim.env.now,
                    ttl=self.ttl,
                    src_service=self.service,
                    dst_service=self.dst_service,
                    content=content,
                )
                # self.log("sending %s" % tm_hk_msg.id)
                self.msgs_sent += 1
                self.send(tm_hk_msg)
                yield self.netsim.env.timeout(self.interval)
