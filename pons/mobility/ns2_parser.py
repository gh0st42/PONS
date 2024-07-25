import math
from dataclasses import dataclass
from enum import Enum
from string import digits
from typing import List, Tuple, Union

from pons.utils import Vector


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
    QUOTE = '"'
    SET_DEST = "setdest"
    BACKSLASH = "\\"
    NEWLINE = "\n"
    HASH = "#"


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
        """splits the ns2 file into tokens"""
        tmp: List[str] = text.split(" ")
        tokens: List[str] = []
        for token in tmp:
            substr_index = 0
            for i in range(1, len(token)):
                last_symbol = token[i - 1]
                current_symbol = token[i]
                if (
                    (last_symbol in TOKENS and current_symbol in digits)
                    or (last_symbol in digits and current_symbol in TOKENS)
                    or (current_symbol in TOKENS)
                    or (last_symbol in TOKENS)
                ):
                    tokens.append(token[substr_index:i])
                    substr_index = i
            tokens.append(token[substr_index:])
        return list(filter(lambda tok: tok != "", tokens))

    def _check(self, tokens: Union[Token, List[Token]]) -> bool:
        """
        checks if the current token is the given token(s) and returns true in that case
        @param tokens: either a token or a list of tokens to check for
        """
        if not isinstance(tokens, list):
            tokens = [tokens]
        values = [t.value for t in tokens]
        return self._current_token in values

    def _accept(self, tokens: Union[Token, List[Token]] = None):
        """
        accepts the current token, optionally with a condition
        @param tokens: either a token, a list of tokens or none if any token should be accepted
        """
        if tokens is not None:
            if not isinstance(tokens, list):
                tokens = [tokens]
            if not self._check(tokens):
                # if the current token is not one of the given tokens
                raise Exception(
                    f"expected {', '.join([token.value for token in tokens])} - got {self._current_token}"
                )
        # select new current token
        self._current_index += 1
        self._current_token = self._tokens[self._current_index]
        next_index = self._current_index + 1
        self._next_token = (
            self._tokens[next_index] if next_index < len(self._tokens) else None
        )

    def parse(self) -> List[Ns2Entry]:
        """parses the file and returns a list of ns2 entries"""
        # parse the first row
        entries = [self._parse_row()]
        # as long as a newline and a next token exists
        while self._check(Token.NEWLINE) and self._next_token is not None:
            self._accept()
            # skip commented rows
            if self._check(Token.HASH):
                self._skip_until_newline()
                continue
            # parse the row
            entry = self._parse_row()
            if entry is not None:
                entries.append(entry)
        return entries

    def _skip_until_newline(self):
        while not self._check(Token.NEWLINE):
            self._accept()

    def _parse_row(self) -> Ns2Entry:
        """parses a ns2 row"""
        # row starts with $node
        if self._check(Token.NODE):
            return self._parse_init_row()
        # row starts with $ns
        if self._check(Token.NS):
            return self._parse_default_row()
        raise Exception(
            f"entries either have to start with {Token.NODE.value} or {Token.NS.value}"
        )

    def _parse_init_row(self) -> Union[Ns2Entry, None]:
        """parses a row of the form $node_(<node_id>) set <coordinate>_ <value>"""
        # initialize entry with node number
        entry = Ns2Entry(node=self._parse_node(), is_init=True)
        self._accept(Token.SET)
        # skip z row
        if self._skip_row():
            return None
        # parse and set the coordinate
        self._parse_coordinate(entry)
        return entry

    def _skip_row(self) -> bool:
        """skips rows setting the z coordinate and returns True if the row has been skipped"""
        if not self._check(Token.Z):
            return False
        # if row is skipped, accept all remaining tokens of the row
        self._accept()
        self._accept(Token.UNDERLINE)
        self._parse_float()
        return True

    def _parse_default_row(self) -> Ns2Entry:
        """parses a row of the format $ns_ at <time> "\$node_(<node_id>) setdest <x> <y> <speed>" """
        self._accept(Token.NS)
        self._accept(Token.UNDERLINE)
        self._accept(Token.AT)
        # parse the time
        time = self._parse_float()
        self._accept(Token.QUOTE)
        # the one generated ns2 code uses a backslash here
        if self._check(Token.BACKSLASH):
            self._accept(Token.BACKSLASH)
        # parse the node
        node = self._parse_node()
        self._accept(Token.SET_DEST)
        # parse coordinates and the speed
        x = self._parse_float()
        y = self._parse_float()
        speed = self._parse_float()
        self._accept(Token.QUOTE)
        # build and return an entry based on parsed data
        return Ns2Entry(node=node, time=time, x=x, y=y, speed=speed)

    def _parse_coordinate(self, entry: Ns2Entry):
        """
        parses a coordinate and sets it on an entry
        @param entry: the entry to set the coordinate on
        """
        # check, if token is either x, y or z
        if not self._check([Token.X, Token.Y, Token.Z]):
            raise Exception(
                f"expected {Token.X.value}, {Token.Y.value} or {Token.Z.value} - got {self._current_token}"
            )
        # save the coordinate (x,y,z)
        coordinate = self._current_token
        self._accept()
        self._accept(Token.UNDERLINE)
        # parse the coordinate value
        value = self._parse_float()
        # set either x or y value on entry - depending on the parsed coordinate
        if coordinate == Token.X.value:
            entry.x = value
        else:
            entry.y = value

    def _parse_node(self) -> int:
        """parses a node and returns the id"""
        self._accept(Token.NODE)
        self._accept(Token.UNDERLINE)
        self._accept(Token.PARAN_LEFT)
        # get node id
        node = self._parse_int()
        self._accept(Token.PARAN_RIGHT)
        return node

    def _parse_int(self) -> int:
        """parses an integer"""
        token = self._current_token
        self._accept()
        return int(token)

    def _parse_float(self) -> float:
        """parses a float"""
        token = self._current_token
        self._accept()
        return float(token)


class Ns2Movement:
    """ns2 movement"""

    def __init__(self, num_nodes, moves, start, end):
        self.num_nodes = num_nodes
        self.moves = moves
        self.start = start
        self.end = end

    @classmethod
    def _get_init_coordinates(
        cls, node: int, entries: List[Ns2Entry]
    ) -> Tuple[float, float]:
        """
        returns the initial coordinates for a node set by the init entries
        @param node: the node id
        @param entries: entries to search in
        """
        x = None
        y = None
        # get all init entries for the node
        init_entries = list(filter(lambda e: e.is_init and e.node == node, entries))
        for entry in init_entries:
            # if entry has a x value, set x
            if entry.x is not None:
                x = entry.x
            # if entry has a y value, set y
            if entry.y is not None:
                y = entry.y
        return x, y

    @classmethod
    def _get_initial_until(
        cls,
        start: int,
        until: float,
        node: int,
        x: float,
        y: float,
        end_time: float = None,
    ) -> List:
        """
        returns a list of initial moves from a start time until a given time
        @param start: start time
        @param until: time until the moves should be added
        @param node: the node id
        @param x: the x coordinate
        @param y: the y coordinate
        @param end_time: the optional end time of the simulation
        """
        # add moves with integer time until floor(until)
        if end_time is not None:
            until = min(until, end_time)
        if until < start:
            return [(start, node, x, y)]
        moves = [
            (float(time), node, x, y) for time in range(start, math.floor(until) + 1)
        ]
        # add exact time until move
        moves.append((until, node, x, y))
        return moves

    @classmethod
    def _get_moves_for_entry(
        cls,
        node: int,
        node_moves,
        entry: Ns2Entry,
        next_entry: Ns2Entry,
        start_time: float = None,
        end_time: float = None,
    ):
        """
        generates moves for an entry and appends it to node_moves
        @param node: the node to generate for
        @param node_moves: the already generated node_moves
        @param entry: the ns2 entry to generate moves for
        @param end_time: the optional end time of the simulation
        """
        # only append moves if end_time is not surpassed
        if end_time is not None and entry.time >= end_time:
            return node_moves
        current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
        target = Vector(entry.x, entry.y)
        # vector the simulation should move forward in one time step
        direction = (target - current_pos).normalize() * entry.speed

        # time of arrival at target
        target_time = abs(target - current_pos) / entry.speed

        # first integer time
        first_full = math.ceil(entry.time)
        if start_time is not None:
            first_full = max(first_full, math.floor(start_time))
        # step from entry start time until first integer time
        first_step = first_full - entry.time
        # calculate next position
        next = current_pos + first_step * direction
        # append move
        node_moves.append((first_full, node, next.x, next.y))

        # get last integer move
        # if no next entry, move until destination is reached
        until = first_full + target_time
        if next_entry is not None:
            # if there is a next entry, move until its time
            until = next_entry.time
        if end_time is not None:
            # if there is a custom end_time and it is before the until time, use it
            until = min(until, end_time - 1)
        last_full = math.floor(until)

        # for each time step from first int move to last int move
        for time in range(first_full, last_full + 1):
            # only move forward, if the time is not greater than the target time
            if time < entry.time + target_time:
                # calculate new position
                current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
                next = current_pos + direction
            # append move
            node_moves.append((time, node, next.x, next.y))

        current_pos = Vector(node_moves[-1][2], node_moves[-1][3])
        # step from start time of next entry until last integer time
        last_step = until - last_full
        if last_step != 0 and until >= start_time:
            # calculate next time and append move
            next = current_pos + last_step * direction
            node_moves.append((until, node, next.x, next.y))

        # fill up until end_time
        if (
            next_entry is None
            and end_time is not None
            and end_time > until
            and end_time >= start_time
        ):
            for time in range(last_full + 1, end_time):
                node_moves.append((time, node, next.x, next.y))

    @classmethod
    def _fill_up_until_end(cls, nodes, moves, end_time: float):
        for node in nodes:
            node_moves = [move for move in moves if move[1] == node]
            last_move = node_moves[-1]
            last_int = math.floor(end_time)
            for time in range(math.ceil(last_move[0]), last_int + 1):
                moves.append((time, node, last_move[2], last_move[3]))
            if last_int != end_time:
                moves.append((end_time, node, last_move[2], last_move[3]))

    @classmethod
    def _get_moves(cls, entries, start_time: float = None, end_time: float = None):
        """
        generates move based on entries
        @param entries: the entries
        @start_time: the optional start time of the simulation
        @end_time: the optional end time of the simulation
        """
        # get min and max time and nodes
        if start_time is None:
            start_time = min(
                0, math.floor(min(entry.time for entry in entries if not entry.is_init))
            )
        # if end_time is None:
        #    math.floor(max(entry.time for entry in entries if not entry.is_init))
        nodes = set(entry.node for entry in entries)
        moves = []

        # create dict assigning entries to nodes
        non_init_entries = sorted(
            list(filter(lambda e: not e.is_init, entries)), key=lambda e: e.time
        )
        entry_dict = {node: [] for node in nodes}
        for entry in non_init_entries:
            entry_dict[entry.node].append(entry)

        # for every node
        for node in nodes:
            node_moves = []
            node_entries = entry_dict[node]
            # get initial coordinates
            x, y = cls._get_init_coordinates(node, entries)
            # fill moves with init coordinates until first entry
            node_moves += cls._get_initial_until(
                start_time, entry_dict[node][0].time, node, x, y, end_time
            )
            # for every entry except last one
            for i in range(0, len(node_entries) - 1):
                # get current and next entry
                current_entry = node_entries[i]
                next_entry = node_entries[i + 1]

                cls._get_moves_for_entry(
                    node, node_moves, current_entry, next_entry, start_time, end_time
                )

            last_entry = node_entries[-1]
            cls._get_moves_for_entry(
                node, node_moves, last_entry, None, start_time, end_time
            )

            moves += node_moves
        # build class from num_nodes, moves, min and max time
        max_time = max(move[0] for move in moves)
        if end_time is not None:
            max_time = end_time - 1
        cls._fill_up_until_end(nodes, moves, max_time)
        return cls(len(nodes), sorted(moves, key=lambda m: m[0]), start_time, max_time)

    @classmethod
    def from_file(cls, path: str, start_time: float = None, end_time: float = None):
        """
        get movement from a ns2 file
        @param path: path to the file
        @param start_time: optional start time of the simulation
        @param end_time: optional end time of the simulation
            (if none is given, the simulation runs until every nodes have reached their destination)
        """
        # read and parse file
        with open(path, "r") as file:
            content = file.read()
            entries = Ns2Parser(content).parse()
        # get moves
        moves = cls._get_moves(entries, start_time, end_time)
        # append z = 0 to every move
        moves.moves = [(time, node, x, y, 0) for time, node, x, y in moves.moves]
        return moves
