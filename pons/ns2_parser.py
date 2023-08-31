import math
from dataclasses import dataclass
from enum import Enum
from string import digits
from typing import List, Tuple, Dict
from utils import Vector, flatten


class Token(Enum):
    """enum for all tokens"""
    NODE = "$node"
    PARAN_LEFT = "("
    PARAN_RIGHT = ")"
    SET = "set"
    X = "X"
    Y = "Y"
    Z = "Z"
    UNDERLINE = "_"
    NS = "$ns"
    AT = "at"
    QUOTE = "\""
    SET_DEST = "setdest"
    BACKSLASH = "\\"
    NEWLINE = "\n"


TOKENS = [e.value for e in Token]


@dataclass
class Ns2Entry:
    """dataclass for ns2 entries"""
    node: int
    time: float = None
    x: float = None
    y: float = None
    speed: float = None
    is_init: bool = False


class Ns2Parser:
    """ns2 parser"""

    def __init__(self, content: str):
        self._tokens = self._scan(content)
        self._current_index = 0
        self._current_token = self._tokens[0]
        self._next_token = self._tokens[1]

    @staticmethod
    def _scan(text: str) -> List[str]:
        tmp: List[str] = text.split(" ")
        tokens: List[str] = []
        for token in tmp:
            substr_index = 0
            for i in range(1, len(token)):
                last_symbol = token[i - 1]
                current_symbol = token[i]
                if (last_symbol in TOKENS and current_symbol in digits) \
                        or (last_symbol in digits and current_symbol in TOKENS) \
                        or (current_symbol in TOKENS) or (last_symbol in TOKENS):
                    tokens.append(token[substr_index:i])
                    substr_index = i
            tokens.append(token[substr_index:])
        return list(filter(lambda tok: tok != "", tokens))

    def _check(self, tokens: Token | List[Token]) -> bool:
        if not isinstance(tokens, list):
            tokens = [tokens]
        values = [t.value for t in tokens]
        return self._current_token in values

    def _accept(self, tokens: Token | List[Token] = None):
        if tokens is not None:
            if not isinstance(tokens, list):
                tokens = [tokens]
            if not self._check(tokens):
                raise Exception(f"expected {', '.join([token.value for token in tokens])} - got {self._current_token}")
        self._current_index += 1
        self._current_token = self._tokens[self._current_index]
        next_index = self._current_index + 1
        self._next_token = self._tokens[next_index] if next_index < len(self._tokens) else None

    def parse(self) -> List[Ns2Entry]:
        entries = [self._parse_row()]
        while self._check(Token.NEWLINE) and self._next_token is not None:
            self._accept()
            entries.append(self._parse_row())
        return entries

    def _parse_row(self) -> Ns2Entry:
        if self._check(Token.NODE):
            return self._parse_init_row()
        if self._check(Token.NS):
            return self._parse_default_row()
        raise Exception(f"entries either have to start with {Token.NODE.value} or {Token.NS.value}")

    def _parse_init_row(self) -> Ns2Entry:
        entry = Ns2Entry(node=self._parse_node(), is_init=True)
        self._accept(Token.SET)
        self._parse_coordinate(entry)
        return entry

    def _parse_default_row(self) -> Ns2Entry:
        self._accept(Token.NS)
        self._accept(Token.UNDERLINE)
        self._accept(Token.AT)
        time = round(self._parse_float())
        self._accept(Token.QUOTE)
        self._accept(Token.BACKSLASH)
        node = self._parse_node()
        self._accept(Token.SET_DEST)
        x = self._parse_float()
        y = self._parse_float()
        speed = self._parse_float()
        self._accept(Token.QUOTE)
        return Ns2Entry(node=node, time=time, x=x, y=y, speed=speed)

    def _parse_coordinate(self, entry: Ns2Entry):
        if not self._check([Token.X, Token.Y, Token.Z]):
            raise Exception(f"expected {Token.X.value}, {Token.Y.value} or {Token.Z.value} - got {self._current_token}")
        coordinate = self._current_token
        self._accept()
        self._accept(Token.UNDERLINE)
        value = self._parse_float()
        if coordinate == Token.X.value:
            entry.x = value
        else:
            entry.y = value

    def _parse_node(self) -> int:
        self._accept(Token.NODE)
        self._accept(Token.UNDERLINE)
        self._accept(Token.PARAN_LEFT)
        node = self._parse_int()
        self._accept(Token.PARAN_RIGHT)
        return node

    def _parse_int(self) -> int:
        token = self._current_token
        self._accept()
        return int(token)

    def _parse_float(self) -> float:
        token = self._current_token
        self._accept()
        return float(token)


class Ns2Movement:
    def __init__(self, num_nodes, moves=[]):
        self.num_nodes = num_nodes
        self.moves = moves

    @classmethod
    def _get_initial(cls, start_time: float, entries: List[Ns2Entry]) -> Dict[float, Dict[int, List]]:
        init_entries = list(filter(lambda e: e.is_init, entries))
        moves_dict = {start_time: {}}
        for entry in init_entries:
            if entry.node not in moves_dict[start_time]:
                moves_dict[start_time][entry.node] = [start_time, entry.node, entry.x, entry.y]
            if entry.x is not None:
                moves_dict[start_time][entry.node][2] = entry.x
            if entry.y is not None:
                moves_dict[start_time][entry.node][3] = entry.y
        return moves_dict

    @classmethod
    def _get_moves(cls, entries: List[Ns2Entry]) -> Tuple[List[Tuple], int]:
        min_time = math.floor(min(entry.time for entry in entries if not entry.is_init))
        max_time = math.floor(max(entry.time for entry in entries if not entry.is_init))
        nodes = set([entry.node for entry in entries])
        moves = cls._get_initial(min_time - 1, entries)

        entry_dict = {}
        non_init_entries = list(filter(lambda e: not e.is_init, entries))
        for entry in non_init_entries:
            time = entry.time
            if time not in entry_dict:
                entry_dict[time] = {}
            entry_dict[time][entry.node] = entry

        for node in nodes:
            last_entry_time = None
            for time in range(min_time, max_time + 1):
                if time in entry_dict and node in entry_dict[time]:
                    last_entry_time = time
                if time not in moves:
                    moves[time] = {}
                if last_entry_time is None:
                    moves[time][node] = moves[time - 1][node]
                    continue
                current_pos = Vector(moves[time - 1][node][2], moves[time - 1][node][3])
                entry = entry_dict[last_entry_time][node]
                destination = Vector(entry.x, entry.y)
                delta = destination - current_pos
                step = delta.normalize() * entry.speed
                new_pos = current_pos + step
                moves[time][node] = [time, node, new_pos.x, new_pos.y]

        return flatten([[tuple(moves[time][node]) for node in moves[time]] for time in moves]), len(nodes)

    @classmethod
    def from_file(cls, filename: str):
        with open(filename, "r") as file:
            content = file.read()
            entries = Ns2Parser(content).parse()
        moves, num_nodes = cls._get_moves(entries)
        return moves


#moves = Ns2Movement.from_file("default_scenario_MovementNs2Report.txt")
