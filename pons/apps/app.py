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
            {
                "event": "RX",
                "id": self.my_id,
                "service": self.service,
                "from": msg.src,
                "from_service": msg.src_service,
                "msg": msg.unique_id(),
            },
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


class SinkApp(App):
    def __init__(self, service: int = 7):
        super().__init__(service)
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}

    def __str__(self):
        return "SinkApp (%d, %d)" % (self.my_id, self.service)

    def on_msg_received(self, msg: pons.Message):
        self.log("message received in sink app: %s" % msg)
        self.msgs_received += 1


class SenderApp(App):
    def __init__(
        self,
        interval: float = 1.0,
        service: int = 1,
        dst: int = 0,
        dst_service: int = 1,
        payload: str | None = None,
        ttl: int = 3600,
        size: int | None = 64000,
        active_time: tuple[float, float] | None = None,
        msg_prefix: str = "MSG",
    ):
        super().__init__(service)
        self.msgs_sent = 0
        self.msgs_received = 0
        self.msgs_failed = 0
        self.msgs = {}
        self.dst = dst
        self.dst_service = dst_service
        self.payload = payload
        self.ttl = ttl
        self.size = size
        self.active_time = active_time
        self.msg_prefix = msg_prefix
        self.interval = interval

        if self.payload:
            self.size = len(self.payload.encode())

    def __str__(self):
        return "SenderApp (%d, %d)" % (self.my_id, self.service)

    def on_msg_received(self, msg: pons.Message):
        self.log("message received in sender app: %s" % msg)

    def start(self, netsim: pons.NetSim, my_id: int):
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        self.netsim.env.process(self.run())

    def run(self):
        if self.active_time is not None and self.active_time[0] > 0:
            yield self.netsim.env.timeout(self.active_time[0])

        while True:
            if (
                self.active_time is not None
                and self.netsim.env.now > self.active_time[1]
                and self.active_time[1] > 0
            ):
                self.log("stopping sender app")
                return
            msg = pons.Message(
                f"{self.msg_prefix}-%d" % self.msgs_sent,
                self.my_id,
                self.dst,
                self.size,
                created=self.netsim.env.now,
                ttl=self.ttl,
                src_service=self.service,
                dst_service=self.dst_service,
                content=self.payload,
            )
            self.log("sending message: %s" % msg)
            self.send(msg)
            self.msgs_sent += 1
            yield self.netsim.env.timeout(self.interval)
