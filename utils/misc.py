def get_marks_dict(min: int, max: int, step: int):
    return {step: str(step) for step in range(min, max + 1, step)}