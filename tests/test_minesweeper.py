# There is no tests atm, but the file exist to assert the code can be executed in older python versions (because ruff doesn't interpret the code, it doesn't detect retro-compatibility.)

import minesweeper
import pytest


@pytest.fixture
def game():
    game = minesweeper.Minesweeper((5, 5), 5, random_seed=10)
    print(game.board)
    return game


def test_random_seed_1(game: minesweeper.Minesweeper):
    assert game.board == [
        [0, 1, 1, 1, 0],
        [1, 2, -1, 1, 0],
        [1, -1, 2, 2, 1],
        [2, 2, 1, 2, -1],
        [-1, 1, 0, 2, -1],
    ]


def test_random_seed_2():
    game1 = minesweeper.Minesweeper((5, 5), 5, random_seed=10)
    game2 = minesweeper.Minesweeper((5, 5), 5, random_seed=10)
    assert game1.board == game2.board


def test_flag(game: minesweeper.Minesweeper):
    game.toggle_flag(1, 1)
    assert game.flags == [(1, 1)]


def test_number_play(game: minesweeper.Minesweeper):
    game.play(0, 1)
    assert game.revealed == [(0, 1)]


def test_empty_play(game: minesweeper.Minesweeper):
    game.play(0, 0)
    assert set(game.revealed) == {(0, 0), (0, 1), (1, 0), (1, 1)}


def test_chord(game: minesweeper.Minesweeper):
    game.toggle_flag(3, 4)
    game.play(2, 4)
    game.play(2, 4)
    assert set(game.revealed) == {(2, 4), (3, 3), (2, 3), (1, 3), (0, 3), (0, 4), (1, 4)}


def test_no_chord_less(game: minesweeper.Minesweeper):
    game.play(2, 4)
    game.play(2, 4)
    assert set(game.revealed) == {(2, 4)}


def test_no_chord_more(game: minesweeper.Minesweeper):
    game.toggle_flag(3, 4)
    game.toggle_flag(3, 3)
    game.play(2, 4)
    game.play(2, 4)
    assert set(game.revealed) == {(2, 4)}


def test_no_win_if_not_all_revealed(game: minesweeper.Minesweeper):
    game.toggle_flag(1, 2)
    game.toggle_flag(2, 1)
    game.toggle_flag(4, 0)
    game.toggle_flag(3, 4)
    game.toggle_flag(4, 4)
    assert game.game_over is False


def win_position(game: minesweeper.Minesweeper):
    game.toggle_flag(1, 2)
    game.toggle_flag(2, 1)
    game.toggle_flag(4, 0)
    game.toggle_flag(3, 4)
    game.toggle_flag(4, 4)
    game.play(0, 0)
    game.play(0, 2)
    game.play(3, 1)
    game.play(3, 1)  # use chord
    game.play(2, 3)
    game.play(2, 3)  # use chord


def test_win(game: minesweeper.Minesweeper):
    win_position(game)
    assert game.game_over is True


def test_win_but_not_all_flagged(game: minesweeper.Minesweeper):
    game.toggle_flag(1, 2)
    game.toggle_flag(2, 1)
    game.toggle_flag(4, 0)
    game.toggle_flag(3, 4)
    game.play(0, 0)
    game.play(0, 2)
    game.play(3, 1)
    game.play(3, 1)  # use chord
    game.play(2, 3)
    game.play(2, 3)  # use chord
    assert game.game_over is True


def test_no_play_after_win(game: minesweeper.Minesweeper):
    win_position(game)
    with pytest.raises(minesweeper.GameOver):
        game.play(0, 0)


def test_idempotence(game: minesweeper.Minesweeper):
    """TODO"""


def test_initial_play_new(game: minesweeper.Minesweeper):
    game.new((1, 0))  # random seed put a bomb here.
    assert game.game_over is not True


def test_initial_play_class():
    game = minesweeper.Minesweeper((5, 5), 5, initial_play=(4, 0), random_seed=10)
    assert game.game_over is not True
