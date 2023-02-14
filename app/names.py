import json
import math
import random
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=10000)
def load(name):
    fn = Path(__file__).parent / "names.json"
    return json.load(fn.open()).get(name)


NUMBERS = load("numbers")
ANIMALS = load("animals")
COLORS = load("colors")


def new_name():
    return (
        random.choice(COLORS).replace(" ", "-")
        + "-"
        + random.choice(ANIMALS).lower()
        + "-"
        + str(random.randint(1, 1000))
    )
