import math
from dataclasses import dataclass
from enum import Enum
from string import digits
from typing import List, Tuple, Dict

from utils import Vector


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
            entry = self._parse_row()
            if entry is not None:
                entries.append(entry)
        return entries

    def _parse_row(self) -> Ns2Entry:
        if self._check(Token.NODE):
            return self._parse_init_row()
        if self._check(Token.NS):
            return self._parse_default_row()
        raise Exception(f"entries either have to start with {Token.NODE.value} or {Token.NS.value}")

    def _parse_init_row(self) -> Ns2Entry | None:
        entry = Ns2Entry(node=self._parse_node(), is_init=True)
        self._accept(Token.SET)
        if self._skip_row():
            return None
        self._parse_coordinate(entry)
        return entry

    def _skip_row(self) -> bool:
        if not self._check(Token.Z):
            return False
        self._accept()
        self._accept(Token.UNDERLINE)
        self._parse_float()
        return True

    def _parse_default_row(self) -> Ns2Entry:
        self._accept(Token.NS)
        self._accept(Token.UNDERLINE)
        self._accept(Token.AT)
        time = self._parse_float()
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
    def _get_init_coordinates(cls, node: int, entries: List[Ns2Entry]) -> Tuple[float, float]:
        x = None
        y = None
        init_entries = list(filter(lambda e: e.is_init and e.node == node, entries))
        print(init_entries)
        for entry in init_entries:
            if entry.x is not None:
                x = entry.x
            if entry.y is not None:
                y = entry.y
        return x, y

    @classmethod
    def _get_initial_until(cls, start: int, until: float, node: int, x: float, y: float) -> List:
        moves = [(float(time), node, x, y) for time in range(start, math.floor(until))]
        moves.append((until, node, x, y))
        return moves

    @classmethod
    def _get_moves(cls, entries):
        min_time = min(math.floor(min(entry.time for entry in entries if not entry.is_init)), 1)
        max_time = math.floor(max(entry.time for entry in entries if not entry.is_init))
        nodes = set([entry.node for entry in entries])
        moves = []

        non_init_entries = sorted(list(filter(lambda e: not e.is_init, entries)), key=lambda e: e.time)
        entry_dict = {node: [] for node in nodes}
        for entry in non_init_entries:
            entry_dict[entry.node].append(entry)

        for node in nodes:
            node_moves = []
            node_entries = entry_dict[node]
            x, y = cls._get_init_coordinates(node, entries)
            node_moves += cls._get_initial_until(min_time - 1, entry_dict[node][0].time, node, x, y)
            for i in range(0, len(node_entries) - 1):
                current_entry = node_entries[i]
                next_entry = node_entries[i + 1]

                current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
                target = Vector(current_entry.x, current_entry.y)
                direction = (target - current_pos).normalize() * current_entry.speed

                target_time = ((target - current_pos) / direction).x if not direction == 0 else math.inf

                first_full = math.ceil(current_entry.time)
                first_step = first_full - current_entry.time
                next = current_pos + first_step * direction
                node_moves.append((first_full, node, next.x, next.y))

                last_full = math.floor(next_entry.time)

                for time in range(first_full, last_full + 1):
                    if time < current_entry.time + target_time:
                        current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
                        next = current_pos + direction
                    node_moves.append((time, node, next.x, next.y))

                current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
                last_step = next_entry.time - last_full
                next = current_pos + last_step * direction
                node_moves.append((next_entry.time, node, next.x, next.y))

            moves += node_moves
        return len(nodes), sorted(moves, key=lambda m: m[0])

    @classmethod
    def from_file(cls, filename: str):
        with open(filename, "r") as file:
            content = file.read()
            entries = Ns2Parser(content).parse()
        num_nodes, moves = cls._get_moves(entries)
        return cls(num_nodes, moves)
