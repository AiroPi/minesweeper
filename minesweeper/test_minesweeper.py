# There is no tests atm, but the file exist to assert the code can be executed in older python versions (because ruff doesn't interpret the code, it doesn't detect retro-compatibility.)

import pytest

import minesweeper as minesweeper


def test_nothing():
    pass


del minesweeper
del pytest
