from copy import copy
import random
import pons
from pons.event_log import event_log


class App(object):
    def __init__(self, service: int):
        self.service = service

    def __str__(self):
        return "App (%d, %d)" % (self.my_id, self.service)

    def __repr__(self):
        return str(self)

    def log(self, msg):
        return
        print(
            "[ %f ] [%s.%d] APP: %s"
            % (self.netsim.env.now, self.my_id, self.service, msg)
        )

    def start(self, netsim: pons.NetSim, my_id: int):
        self.my_id = my_id
        self.netsim = netsim

    def _on_msg_received(self, msg: pons.Message):
        event_log(
            self.netsim.env.now,
            "APP",
            {"event": "RX", "id": self.my_id, "msg": msg.unique_id()},
        )
        self.on_msg_received(msg)

    def send(self, msg: pons.Message):
        self.netsim.routing_stats["created"] += 1
        event_log(
            self.netsim.env.now,
            "APP",
            {"event": "TX", "src": self.my_id, "dst": msg.dst, "msg": msg.unique_id()},
        )
        self.netsim.nodes[self.my_id].router.add(msg)

    def on_msg_received(self, msg: pons.Message):
        self.log("msg received: %s" % (msg))


class PingApp(App):
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
        return "PingApp (%d, %d)" % (self.my_id, self.service)

    def start(self, netsim: pons.NetSim, my_id: int):
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
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
