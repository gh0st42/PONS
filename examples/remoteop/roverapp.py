import random
import sys
import pathlib
import math

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

    def __str__(self):
        return "Rover (%s / %s) [%f, %f]" % (self.name, self.my_id, self.x, self.y)

    def __repr__(self):
        return str(self)

    def log(self, msg):
        return
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

    def forward(self, speed: float, time: float):
        self.speed = speed
        self.v_time = time

    def turn(self, angle: float):
        self.direction += angle
        self.direction %= 360

    def update_position(self, time: float):
        if self.v_time > 0:
            self.x += self.speed * time * math.cos(math.radians(self.direction))
            self.y += self.speed * time * math.sin(math.radians(self.direction))
            self.v_time -= time
        else:
            self.speed = 0

    def update_direction(self, time: float):
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

    def process_commands(self):
        if len(self.cmds) > 0:
            cmd = self.cmds[0]
            self.cmds = self.cmds[1:]
            if cmd[0] == "forward":
                self.forward(cmd[1], cmd[2])
            elif cmd[0] == "turn":
                self.turn(cmd[1])

    def add_command(self, cmd):
        if cmd[0] == "cancel":
            self.target_angle = self.direction
            self.v_time = 0
        elif cmd[0] == "clear":
            self.cmds = []
        else:
            self.cmds.append(cmd)

    def run(self):
        while True:
            self.log(
                "position: [%f, %f], direction: %f, battery: %.01f"
                % (self.x, self.y, self.direction, self.battery)
            )
            if self.battery <= 0:
                self.log("battery depleted")
                yield self.netsim.env.timeout(10)
                continue
            if self.v_time > 0:
                self.update_position(1)
                self.battery -= 0.2
            elif self.direction != self.target_angle:
                self.update_direction(1)
                self.battery -= 0.1
            else:
                self.process_commands()
            yield self.netsim.env.timeout(1)


class RoverApp(App):
    def __init__(
        self,
        dst: int,
        service: int = 7,
        dst_service: int = 7,
        interval: float = 1.0,
        ttl: int = 3600,
        size: int = 1000,
        rnd_start: bool = False,
    ):
        super().__init__(service)
        self.msgs_sent = 0
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}
        self.interval = interval
        self.ttl = ttl
        self.size = size
        self.dst = dst
        self.dst_service = dst_service
        self.rnd_start = rnd_start

    def __str__(self):
        return "RoverApp (%d, %d)" % (self.my_id, self.service)

    def log(self, msg):
        return
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
        if msg.id.startswith("ping-"):
            self.log("ping received: %s" % (msg.id))
            self.msgs_received += 1
            if self.ttl > 0:
                content = {
                    "id": msg.id,
                    "start": msg.created,
                    "end": self.netsim.env.now,
                }
                pong_msg = pons.Message(
                    msg.id.replace("ping", "pong"),
                    self.my_id,
                    msg.src,
                    msg.size,
                    self.netsim.env.now,
                    ttl=msg.ttl,
                    src_service=msg.dst_service,
                    dst_service=msg.src_service,
                    content=content,
                )
                self.send(pong_msg)
        elif msg.id.startswith("pong-"):
            now = self.netsim.env.now
            self.log(
                "%s received from node %s with %d bytes in %fs"
                % (msg.id, msg.src, msg.size, now - msg.content["start"])
            )
            # self.log("%s received from node %s with %d bytes in %fs" % (msg.id, msg.src, msg.size, msg.content['end'] - msg.content['start']))
            self.msgs_received += 1

    def run(self):
        if self.interval > 0:
            if self.rnd_start:
                delay = random.random() * self.interval
                yield self.netsim.env.timeout(delay)
            while True:
                ping_msg = pons.Message(
                    "ping-%d" % self.msgs_sent,
                    self.my_id,
                    self.dst,
                    self.size,
                    self.netsim.env.now,
                    ttl=self.ttl,
                    src_service=self.service,
                    dst_service=self.dst_service,
                )
                self.log("sending ping %s" % ping_msg.id)
                self.msgs_sent += 1
                self.send(ping_msg)
                yield self.netsim.env.timeout(self.interval)
