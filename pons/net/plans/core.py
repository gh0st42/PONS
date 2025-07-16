from __future__ import annotations
from dataclasses import dataclass
from dateutil.parser import parse


from random import random
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional

from pons.net.plans import bandwidth_parser
from pons.net.plans import Contact, CommonContactPlan


@dataclass(frozen=True)
class CoreContact(Contact):
    timespan: Tuple[float, float]
    nodes: Tuple[int, int]
    bw: int
    loss: float
    delay: float
    jitter: float
    fixed: bool = False

    def __str__(self) -> str:
        if self.fixed:
            return (
                "CoreContact(fixed, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)"
                % (self.nodes, self.bw, self.loss, self.delay, self.jitter)
            )
        else:
            return (
                "CoreContact(timespan=%r, nodes=%r, bw=%d, loss=%f, delay=%f, jitter=%f)"
                % (
                    self.timespan,
                    self.nodes,
                    self.bw,
                    self.loss,
                    self.delay,
                    self.jitter,
                )
            )

    @classmethod
    def from_string(
        cls, line: str, mapping: Optional[Dict[str, int]] = None
    ) -> "CoreContact":
        if mapping is None:
            mapping = {}
        line = line.strip()
        is_fixed = False
        if line.startswith("a contact"):
            line = line[9:].strip()
        elif line.startswith("a fixed"):
            is_fixed = True
            line = line[7:].strip()

        fields = line.split()
        # print(fields, len(fields))
        if (not is_fixed and len(fields) != 8) or (is_fixed and len(fields) != 6):
            raise ValueError("Invalid CoreContact line: %s" % line)
        idx = 0
        if not is_fixed:
            timespan = (float(fields[idx]), float(fields[idx + 1]))
            idx += 2
        else:
            timespan = (0, -1)  # fixed contacts do not have a timespan

        if fields[idx] in mapping:
            fields[idx] = mapping[fields[idx]]
        else:
            fields[idx] = int(fields[idx])

        if fields[idx + 1] in mapping:
            fields[idx + 1] = mapping[fields[idx + 1]]
        else:
            fields[idx + 1] = int(fields[idx + 1])

        nodes = (fields[idx], fields[idx + 1])
        bw = bandwidth_parser(fields[idx + 2])
        loss = float(fields[idx + 3])
        delay = float(fields[idx + 4])
        jitter = float(fields[idx + 5])
        return cls(timespan, nodes, bw, loss, delay, jitter, is_fixed)
