
from copy import copy
import pons

class App(object):
    def __init__(self, service : int):
        self.service = service

    def __str__(self):
        return "App (%d, %d)" % (self.my_id, self.service)

    def __repr__(self):
        return str(self)

    def log(self, msg):
        print("[ %f ] [%s.%d] APP: %s" % (self.netsim.env.now, self.my_id, self.service, msg))

    def start(self, netsim: pons.NetSim, my_id : int):
        self.my_id = my_id
        self.netsim = netsim

    def on_msg_received(self, msg: pons.Message):
        self.log("msg received: %s" % (msg))
    
class PingApp(App):
  def __init__(self, dst : int, service : int = 7, dst_service : int = 7, interval : float = 1.0, ttl : int = 3600, size : int = 1000):
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
  
  def __str__(self):
      return "PingApp (%d, %d)" % (self.my_id, self.service)
  
  def start(self, netsim: pons.NetSim, my_id : int):
        self.my_id = my_id
        self.netsim = netsim
        self.log("starting")
        self.netsim.env.process(self.run())
  
  def on_msg_received(self, msg: pons.Message):
    if msg.id.startswith("ping-"):
        self.log("ping received: %s" % (msg.id))
        self.msgs_received += 1
        content = { "id": msg.id, "start": msg.created, "end": self.netsim.env.now }
        pong_msg = pons.Message(msg.id.replace('ping', 'pong'), self.my_id, msg.src, msg.size, self.netsim.env.now, ttl=msg.ttl, src_service=msg.dst_service, dst_service=msg.src_service, content=content)
        self.netsim.routing_stats['created'] += 1
        self.netsim.nodes[self.my_id].router.add(pong_msg)
    elif msg.id.startswith("pong-"):
        now = self.netsim.env.now
        self.log("%s received from node %s with %d bytes in %fs" % (msg.id, msg.src, msg.size, now - msg.content['start']))
        #self.log("%s received from node %s with %d bytes in %fs" % (msg.id, msg.src, msg.size, msg.content['end'] - msg.content['start']))
        self.msgs_received += 1        

  
  def run(self):
        if self.interval > 0:
          while True:
              yield self.netsim.env.timeout(self.interval)
              ping_msg = pons.Message("ping-%d" % self.msgs_sent, self.my_id, self.dst, self.size, self.netsim.env.now, ttl=self.ttl, src_service=self.service, dst_service=self.dst_service)
              self.log("sending ping %s" % ping_msg.id)
              self.msgs_sent += 1
              self.netsim.routing_stats['created'] += 1
              self.netsim.nodes[self.my_id].router.add(ping_msg)
