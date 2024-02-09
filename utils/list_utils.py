from typing import List, Callable, Dict, TypeVar

K = TypeVar("K")
V = TypeVar("V")


def to_lookup(values: List[V], key_selector: Callable[[V], K]) -> Dict[K, List[V]]:
    """converts a list to a lookup table based on a key selector function"""
    lookup = {}
    for value in values:
        key = key_selector(value)
        if key not in lookup:
            lookup[key] = []
        lookup[key].append(value)
    return lookup


def contains(values: List[V], predicate: Callable[[V], bool]) -> bool:
    """checks if a list contains a value conforming to a predicate"""
    for value in values:
        if predicate(value):
            return True
    return False
