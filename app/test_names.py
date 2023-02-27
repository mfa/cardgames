import random

from names import new_name


def test_new_name():
    random.seed(1)
    assert new_name() == "coffee-mosquito-868"
