from typing import List, Any


def flatten(items: List[Any]) -> List[Any]:
    if not isinstance(items, list):
        return [items]
    result = []
    for item in items:
        result += flatten(item)
    return result
