import math
from dataclasses import dataclass


@dataclass
class Vector:
    x: float
    y: float

    def __str__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __repr__(self) -> str:
        return str(self)

    def __abs__(self) -> float:
        return math.sqrt((self.x ** 2) + (self.y ** 2))

    def __sub__(self, other: "Vector" or float) -> "Vector":
        if isinstance(other, Vector):
            return Vector(x=self.x - other.x, y=self.y - other.y)
        return Vector(x=self.x - other, y=self.y - other)

    def __add__(self, other: "Vector" or float) -> "Vector":
        if isinstance(other, Vector):
            return Vector(x=self.x + other.x, y=self.y + other.y)
        return Vector(x=self.x + other, y=self.y + other)

    def __mul__(self, other: "Vector" or float) -> "Vector":
        if isinstance(other, Vector):
            return Vector(x=self.x * other.x, y=self.y * other.y)
        return Vector(x=self.x * other, y=self.y * other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other: "Vector" or float) -> "Vector":
        if isinstance(other, Vector):
            return Vector(x=self.x / other.x, y=self.y / other.y)
        return Vector(x=self.x / other, y=self.y / other)

    def __eq__(self, other):
        if isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        return self.x == other and self.y == other

    def normalize(self) -> "Vector":
        if self == 0:
            return self
        return self / abs(self)

