import json
import random
from functools import lru_cache
from pathlib import Path
from typing import List


@lru_cache(maxsize=10000)
def load(name) -> List[str]:
    fn = Path(__file__).parent / "names.json"
    return json.load(fn.open()).get(name)


NUMBERS = load("numbers")
ANIMALS = load("animals")
COLORS = load("colors")


def new_name() -> str:
    return (
        random.choice(COLORS).replace(" ", "-")
        + "-"
        + random.choice(ANIMALS).replace(" ", "-").lower()
        + "-"
        + str(random.randint(1, 1000))
    )
