from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain, permutations
from typing import TYPE_CHECKING, cast

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    Height: TypeAlias = int
    Width: TypeAlias = int
    Row: TypeAlias = int
    Column: TypeAlias = int

    BoardT = list[list[int]]


@dataclass
class MinesweeperConfig:
    height: int
    width: int
    number_of_mines: int
    initial_play: tuple[Row, Column] | None = None


class GameOver(Exception):
    pass


class PlayType(Enum):
    BOMB_EXPLODED = auto()
    EMPTY_SPOT = auto()
    NUMBERED_SPOT = auto()
    ALREADY_REVEALED = auto()


@dataclass
class Play:
    type: PlayType
    positions: tuple[tuple[Row, Column], ...]


class Minesweeper:
    def __init__(
        self,
        size: tuple[Height, Width],
        number_of_mines: int,
        initial_play: tuple[Row, Column] | None = None,
    ):
        self.size: tuple[Height, Width] = size
        self.number_of_mines: int = number_of_mines

        self.revealed: list[tuple[Height, Width]] = []
        self.flags: list[tuple[Height, Width]] = []
        self.game_over: bool = False
        self._board: BoardT = self.create_board(initial_play)
        if initial_play is not None:
            self.play(*initial_play)

    @classmethod
    def from_config(cls, config: MinesweeperConfig):
        return cls((config.height, config.width), config.number_of_mines, config.initial_play)

    @property
    def board(self) -> BoardT:
        return self._board

    @property
    def positions(self) -> set[tuple[Height, Width]]:
        return {(x, y) for x in range(self.size[0]) for y in range(self.size[1])}

    @property
    def mines_positions(self) -> set[tuple[Height, Width]]:
        return {(x, y) for x in range(self.size[0]) for y in range(self.size[1]) if self._board[x][y] == -1}

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.size[0] and 0 <= y < self.size[1]

    def add_flag(self, x: int, y: int) -> None:
        if (x, y) in self.revealed:
            return
        self.flags.append((x, y))

    def play(self, x: int, y: int) -> Play:
        """Play the game at the given position. Return False if a bomb is found."""
        if self.game_over:
            raise GameOver("The game is over.")

        if not self.is_inside(x, y):
            raise ValueError("The given position is out of the board.")

        if (x, y) in self.mines_positions:
            self.game_over = True
            self.revealed.append((x, y))
            return Play(PlayType.BOMB_EXPLODED, ((x, y),))

        if (x, y) in self.revealed:
            return Play(PlayType.ALREADY_REVEALED, ((x, y),))

        if self._board[x][y] == 0:
            positions = self.diffuse_empty_places(x, y)
            return Play(PlayType.EMPTY_SPOT, positions)
        else:
            self.revealed.append((x, y))
            return Play(PlayType.NUMBERED_SPOT, ((x, y),))

    def diffuse_empty_places(self, x: int, y: int, is_corner: bool = False) -> tuple[tuple[Row, Column], ...]:
        """Diffuse the empty place at the given position. This function is recursive."""
        if (x, y) in self.revealed or not self.is_inside(x, y):
            return ()

        self.revealed.append((x, y))

        if self._board[x][y] == 0:
            gen: Iterable[tuple[int, int]] = cast(
                Iterable[tuple[int, int]], chain(permutations(range(-1, 2, 1), 2), ((1, 1), (-1, -1)))
            )
            return (
                (x, y),
                *tuple(cpl for dx, dy in gen for cpl in self.diffuse_empty_places(x + dx, y + dy, dx != 0 and dy != 0)),
            )

        else:
            return ((x, y),)

    def create_board(self, initial_play: tuple[Row, Column] | None) -> BoardT:
        board: BoardT = [[0 for _ in range(self.size[1])] for _ in range(self.size[0])]

        def increment_around(x: int, y: int):
            """Increment the value of the cells around the given position."""

            # I think this can be done in a more elegant way
            def incr(x: int, y: int):
                if 0 <= x < self.size[0] and 0 <= y < self.size[1] and board[x][y] != -1:
                    board[x][y] += 1

            relative_positions: Iterable[tuple[int, int]] = cast(
                Iterable[tuple[int, int]], chain(permutations(range(-1, 2, 1), 2), ((1, 1), (-1, -1)))
            )
            for dx, dy in relative_positions:
                incr(x + dx, y + dy)

        positions = self.positions
        if initial_play is not None:
            positions -= {initial_play}

        mines_pos = random.sample(list(positions), self.number_of_mines)
        for x, y in mines_pos:
            board[x][y] = -1
            increment_around(x, y)

        return board

    def display(self) -> None:
        for x, row in enumerate(self._board):
            special_repr = {
                -1: "X",
                0: " ",
            }
            print(
                *(special_repr.get(case, case) if (x, y) in self.revealed else "■" for y, case in enumerate(row)),
                sep=" ",
            )
