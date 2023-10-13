from dataclasses import dataclass
from typing import Dict

import pons
from .router import Router


@dataclass
class PRoPHETConfig:
    """Class for configuring the PRoPHET Router

    Attributes
    ------------
    p_encounter_first: float
        predictability value for the first encounter between two nodes
    p_first_threshold: float
        if the predictability value for an encountered node is lower than this value,
        it will be set to p_encounter_first
    p_encounter: float
        used for calculating the new predictability
    beta: float
        adjusts the weight of the transitive property
    delta: float
        sets the maximum predictability value to (1 - delta) (should be really low)
    gamma: float
        determines how quickly the predictabilities age (lower gamma -> faster aging)
    """
    p_encounter_first: float = 0.5
    p_first_threshold: float = 0.1
    p_encounter: float = 0.7
    beta: float = 0.9
    delta: float = 0.01
    gamma: float = 0.999


class PRoPHETRouter(Router):
    """
    Implements the PRoPHET Router
    """

    def __init__(self, scan_interval=2.0, capacity=0, config: PRoPHETConfig = None):
        super().__init__(scan_interval, capacity)
        self.store = []
        self.predictabilities = {}
        self.config = PRoPHETConfig() if config is None else config

    def __str__(self):
        return "PRoPHETRouter"

    def start(self, netsim: pons.NetSim, my_id: int):
        super().start(netsim, my_id)
        self.predictabilities[my_id] = {"pred": 1.}

    def add(self, msg):
        # self.log("adding new msg to store")
        self.store.append(msg)
        self.forward(msg)

    def forward(self, msg):
        """
        @param msg: the message to forward
        """
        if msg.dst in self.peers and not self.msg_already_spread(msg, msg.dst):
            # self.log("sending directly to receiver")
            self.netsim.routing_stats['started'] += 1
            # self.netsim.env.process(
            self.netsim.nodes[self.my_id].send(self.netsim, msg.dst, msg)
            # )
            self.remember(msg.dst, msg)
            self.store.remove(msg)
        else:
            # self.log("broadcasting to peers ", self.peers)
            for peer in self.peers:
                if not self.msg_already_spread(msg, peer):
                    peer_preds = self._get_peer_predictabilities(peer)
                    if self._get_pred_for(msg.dst, peer_preds) > self._get_pred_for(msg.dst):
                        # self.log("forwarding to peer")
                        self.netsim.routing_stats['started'] += 1
                        # self.netsim.env.process(
                        self.netsim.nodes[self.my_id].send(
                            self.netsim, peer, msg)
                        # )
                        self.remember(peer, msg)

    def on_peer_discovered(self, peer_id):
        self._update_predictability(peer_id)
        self._age_predictabilities(peer_id)
        self._update_transitive_predictabilities(peer_id)
        # self.log("peer discovered: %d" % peer_id)
        for msg in self.store:
            self.forward(msg)

    def _update_predictability(self, remote_id):
        if (not remote_id in self.predictabilities or
                self.predictabilities[remote_id]["pred"] < self.config.p_first_threshold):
            pred = self.config.p_encounter_first
        else:
            old_pred = self.predictabilities[remote_id]["pred"]
            pred = old_pred + (1 - self.config.delta -
                               old_pred) * self.config.p_encounter
        self.predictabilities[remote_id] = {
            "pred": pred, "last_aging": self.env.now}

    def _age_predictabilities(self, remote_id):
        for peer in self.predictabilities:
            if peer in (self.my_id, remote_id):
                continue
            peer_info = self.predictabilities[remote_id]
            k = self.env.now - peer_info["last_aging"]
            self.predictabilities[remote_id]["pred"] = peer_info["pred"] * \
                (self.config.gamma ** k)
            self.predictabilities[remote_id]["last_aging"] = self.env.now

    def _update_transitive_predictabilities(self, remote_id):
        remote_preds = self._get_peer_predictabilities(remote_id)
        for peer in remote_preds:
            remote_preds[peer] = {
                "pred": max(
                    self._get_pred_for(peer, remote_preds),
                    self._get_pred_for(self.my_id, remote_preds) *
                    self._get_pred_for(peer) * self.config.beta
                ),
                "last_aging": self.env.now
            }

    def _get_peer_predictabilities(self, peer_id: int) -> Dict:
        other_router = self.netsim.nodes[peer_id].router
        assert isinstance(
            other_router, PRoPHETRouter), "PRoPHET only works with other PRoPHET routers"

        return other_router.predictabilities

    def _get_pred_for(self, peer: int, predictabilities: Dict = None) -> float:
        if predictabilities is None:
            predictabilities = self.predictabilities
        return predictabilities[peer]["pred"] if peer in predictabilities else 0

    def on_msg_received(self, msg, remote_id):
        # self.log("msg received: %s from %d" % (msg, remote_id))
        self.netsim.routing_stats['relayed'] += 1
        if not self.is_msg_known(msg):
            self.remember(remote_id, msg)
            msg.hops += 1
            self.store.append(msg)
            if msg.dst == self.my_id:
                # print("msg arrived", self.my_id)
                self.netsim.routing_stats['delivered'] += 1
                self.netsim.routing_stats['hops'] += msg.hops
                self.netsim.routing_stats['latency'] += self.env.now - msg.created
            else:
                # print("msg not arrived yet", self.my_id)
                self.forward(msg)
        else:
            # print("msg already known", self.history)
            self.netsim.routing_stats['dups'] += 1
