from dataclasses import dataclass
import random


@dataclass
class Message(object):
    """A message."""

    id: str
    src: int
    dst: int
    size: int
    created: float
    hops: int = 0
    ttl: int = 3600
    src_service: int = 0
    dst_service: int = 0
    content: dict = None
    metadata = None

    def __str__(self):
        return "Message(%s, src=%d.%d, dst=%d.%d, size=%d)" % (
            self.id,
            self.src,
            self.src_service,
            self.dst,
            self.dst_service,
            self.size,
        )

    def unique_id(self) -> str:
        return "%s-%d-%d" % (self.id, self.src, self.created)

    def is_expired(self, now):
        # print("is_expired: %d + %d > %d" % (self.created, self.ttl, now))
        return now - self.created > self.ttl


def message_event_generator(netsim, msggenconfig):
    """A message generator."""
    env = netsim.env
    counter = 0
    print("start message generator")
    while True:
        # check if interval is a tuple
        if isinstance(msggenconfig["interval"], tuple):
            yield env.timeout(
                random.randint(msggenconfig["interval"][0], msggenconfig["interval"][1])
            )
        else:
            yield env.timeout(msggenconfig["interval"])
        netsim.routing_stats["created"] += 1
        counter += 1
        if isinstance(msggenconfig["src"], tuple):
            src = random.randint(msggenconfig["src"][0], msggenconfig["src"][1] - 1)
        else:
            src = msggenconfig["src"]
        if isinstance(msggenconfig["dst"], tuple):
            dst = random.randint(msggenconfig["dst"][0], msggenconfig["dst"][1] - 1)
        else:
            dst = msggenconfig["dst"]
        if isinstance(msggenconfig["size"], tuple):
            size = random.randint(msggenconfig["size"][0], msggenconfig["size"][1])
        else:
            size = msggenconfig["size"]
        if "ttl" not in msggenconfig:
            ttl = 3600
        elif isinstance(msggenconfig["ttl"], tuple):
            ttl = random.randint(msggenconfig["ttl"][0], msggenconfig["ttl"][1])
        else:
            ttl = msggenconfig["ttl"]
        msgid = "%s%d" % (msggenconfig["id"], counter)
        msg = Message(msgid, src, dst, size, env.now, ttl=ttl)
        netsim.nodes[src].router.add(msg)


def message_burst_generator(netsim, msggenconfig):
    """A message generator."""
    env = netsim.env
    counter = 0
    print("start message burst generator")
    while True:
        # check if interval is a tuple
        if isinstance(msggenconfig["interval"], tuple):
            yield env.timeout(
                random.randint(msggenconfig["interval"][0], msggenconfig["interval"][1])
            )
        else:
            yield env.timeout(msggenconfig["interval"])

        for src in range(msggenconfig["src"][0], msggenconfig["src"][1]):
            netsim.routing_stats["created"] += 1
            counter += 1
            if isinstance(msggenconfig["dst"], tuple):
                dst = random.randint(msggenconfig["dst"][0], msggenconfig["dst"][1] - 1)
            else:
                dst = msggenconfig["dst"]
            if isinstance(msggenconfig["size"], tuple):
                size = random.randint(msggenconfig["size"][0], msggenconfig["size"][1])
            else:
                size = msggenconfig["size"]
            if "ttl" not in msggenconfig:
                ttl = 3600
            elif isinstance(msggenconfig["ttl"], tuple):
                ttl = random.randint(msggenconfig["ttl"][0], msggenconfig["ttl"][1])
            else:
                ttl = msggenconfig["ttl"]
            msgid = "%s%d" % (msggenconfig["id"], counter)
            msg = Message(msgid, src, dst, size, env.now, ttl=ttl)
            # print("create message %s (%d->%d)" % (msgid, src, dst))
            netsim.nodes[src].router.add(msg)
