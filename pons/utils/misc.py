from typing import List, Any


def flatten(items: List[Any]) -> List[Any]:
    if not isinstance(items, list):
        return [items]
    result = []
    for item in items:
        result += flatten(item)
    return result


def get_marks_dict(min: int, max: int, step: int):
    return {step: str(step) for step in range(min, max + 1, step)}