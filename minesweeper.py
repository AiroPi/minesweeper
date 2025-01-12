from __future__ import annotations

import random
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain, permutations
from typing import TYPE_CHECKING, Generator, Iterable, Set, Tuple, cast

from typing_extensions import Self

if TYPE_CHECKING:
    BoardT = list[list[int]]

__all__ = ["GameOver", "GameState", "Minesweeper", "MinesweeperConfig", "Play", "PlayType"]


@dataclass
class MinesweeperConfig:
    """A minesweeper config generator.

    Example:
        ```py
        config = MinesweeperConfig(
            height=10,
            width=10,
            number_of_mines=10
        )
        game = Minesweeper.from_config(config)
        ```

    Args:
        height: the height of the board
        width: the width of the board
        number_of_mines: the number of mines to add in the board
        initial_play: the first play, to ensure there is no mine here
        random_seed: random.seed value
    """

    height: int
    width: int
    number_of_mines: int
    initial_play: Tuple[int, int] | None = None
    random_seed: int | None = None


class GameOver(Exception):
    """You tried to play while the game is over."""


class GameState(Enum):
    LOST = auto()
    WON = auto()
    IN_PROGRESS = auto()


class PlayType(Enum):
    SPREADING = auto()
    POSITION_REVEALED = auto()
    NOTHING = auto()
    CHORD = auto()
    FLAG_ADDED = auto()
    FLAG_REMOVED = auto()


@dataclass(frozen=True)
class Play:
    type: PlayType
    positions: Tuple[Tuple[int, int], ...]
    bomb_exploded: bool = False


class Minesweeper:
    def __init__(
        self,
        size: Tuple[int, int],
        number_of_mines: int,
        initial_play: Tuple[int, int] | None = None,
        random_seed: int | None = None,
    ):
        self._size: Tuple[int, int] = size
        self._mines_nb: int = number_of_mines
        self._random = random.Random(random_seed)

        self.new(initial_play)

    @classmethod
    def from_config(cls, config: MinesweeperConfig):
        """Init a Minesweeper from a MinesweeperConfig

        Args:
            config: the configuration to use

        Returns:
            A new Minesweeper instance.
        """
        return cls((config.height, config.width), config.number_of_mines, config.initial_play, config.random_seed)

    @property
    def state(self) -> GameState:
        """Describe the current state of the game."""
        if set(self.flags) == self.mines_positions and set(self.revealed) == (
            set(self.all_positions) - self.mines_positions
        ):
            return GameState.WON
        if self._history and self._history[-1].bomb_exploded:
            return GameState.LOST
        else:
            return GameState.IN_PROGRESS

    @property
    def game_over(self) -> bool:
        """True if the game is over (lose or win)."""
        return self.state != GameState.IN_PROGRESS

    @property
    def size(self) -> Tuple[int, int]:
        """Get the size of the board. Can't be changed.

        Returns:
            (height, width)
        """
        return self._size

    @property
    def number_of_mines(self) -> int:
        """Get the number of mines."""
        return self._mines_nb

    @property
    def remaining_mines(self) -> int:
        """The number of un-flagged mines. Don't care if the flags are right or not. Can be negative"""
        return self._mines_nb - len(self.flags)

    @property
    def history(self):
        """Return a oldest-to-newest list of `Play`."""
        return deepcopy(self._history)

    @property
    def board(self) -> BoardT:
        """A matrix representing the board.

        The board is represented as a matrix of digits.
        The digits can be -1 for a mine, 0 for no mines around, 1 for one mine around... until 8.

        Example:
            ```py
            [[ 1, -1,  2, -1,  1],
             [ 1,  1,  2,  2,  2],
             [ 0,  0,  0,  1, -1],
             [ 0,  0,  1,  3,  3],
             [ 0,  0,  1, -1, -1]]
            ```
        """
        return deepcopy(self._board)

    @property
    def all_positions(self) -> Generator[Tuple[int, int]]:
        for row in range(self._size[0]):
            for column in range(self._size[1]):
                yield (row, column)

    @property
    def revealed(self):
        return self._revealed.copy()

    @property
    def mines_positions(self) -> Set[Tuple[int, int]]:
        """The positions of the mines.

        Mines positions are stored as a set of coordinates represented as (row, column).

        Example:
            ```py
            {(0, 1), (4, 4), (2, 4), (4, 3), (0, 3)}
            ```
        """
        return {(x, y) for x in range(self._size[0]) for y in range(self._size[1]) if self._board[x][y] == -1}

    def new(self, initial_play: tuple[int, int] | None = None) -> Self:
        """Create a new game, within the same configuration than provided at definition.

        Alter the object in-place.

        Args:
            initial_play: a position that will be pre-played, ensuring no mine is here.
        """
        self._revealed: list[tuple[int, int]] = []
        self.flags: list[tuple[int, int]] = []
        self._history: list[Play] = []
        self._board: BoardT = self._create_board(initial_play)
        if initial_play is not None:
            self._play(*initial_play)

        return self

    def _is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self._size[0] and 0 <= y < self._size[1]

    def toggle_flag(self, row: int, column: int) -> Play:
        """Toggle the presence of a flag on a position.

        Raises:
            ValueError: if the given position is out of bounds

        Args:
            row: the row to toggle the flag at
            column: the column to toggle the flag at

        Return:
            A new `Play`.
        """
        if not self._is_inside(row, column):
            raise ValueError("Position out of bounds.")

        if (row, column) in self.flags:
            self.flags.remove((row, column))
            play = Play(PlayType.FLAG_REMOVED, ((row, column),))
        else:
            self.flags.append((row, column))
            play = Play(PlayType.FLAG_REMOVED, ((row, column),))

        self._history.append(play)
        return play

    def play(self, row: int, column: int):
        """Play at the given position.

        If the position contains a flag, it is ignored.
        If the position is already revealed, it will chord if possible.

        Chord only occur when the number of flags around is greater than the value of the position.

        Args:
            row: the row to play at
            column: the column to play at

        Raises:
            GameOver: if you try to play on a overed game
            ValueError: if the given position is out of bounds

        Returns:
            A `Play` object.
        """
        self._play(row, column)

    def _play(self, row: int, column: int, from_chord: bool = False) -> Play:
        """
        Same as Minesweeper.play but with private option from_chord.

        Args:
            row: the row to play at
            column: the column to play at
            chord_mode: only used for recursive reason (play not added to history)

        Raises:
            GameOver: if you try to play on a overed game
            ValueError: if the given position is out of bounds

        Returns:
            A `Play` object.
        """
        if self.game_over:
            if from_chord:
                return Play(PlayType.NOTHING, ((row, column),))
            raise GameOver("The game is over.")

        if not self._is_inside(row, column):
            raise ValueError("The given position is out of the board.")

        if (row, column) in self.flags:
            return Play(PlayType.NOTHING, ((row, column),))

        if (row, column) in self._revealed and not from_chord:
            play = self._do_chord(row, column)
        elif (row, column) in self.mines_positions:
            self._revealed.append((row, column))
            play = Play(PlayType.POSITION_REVEALED, ((row, column),), bomb_exploded=True)

        elif self._board[row][column] == 0:
            positions = self._spread_empty(row, column)
            play = Play(PlayType.SPREADING, positions)
        else:
            self._revealed.append((row, column))
            play = Play(PlayType.POSITION_REVEALED, ((row, column),))

        if not from_chord:
            self._history.append(play)
        return play

    def _do_chord(self, row: int, column: int):
        value = self._board[row][column]
        flagged = len([adj for adj in self._get_adjacent(row, column) if adj in self.flags])
        if value > 0 and value == flagged:
            l_positions: list[tuple[int, int]] = []
            bomb_exploded = False
            for a_row, a_column in self._get_adjacent(row, column):
                play = self._play(a_row, a_column, from_chord=True)
                print(play)
                if play.type != PlayType.NOTHING:
                    l_positions.extend(play.positions)
                bomb_exploded = bomb_exploded or play.bomb_exploded
            print(bomb_exploded)
            return Play(PlayType.CHORD, tuple(l_positions), bomb_exploded=bomb_exploded)
        else:
            return Play(PlayType.NOTHING, ((row, column),))

    def _get_adjacent(self, row: int, column: int) -> Iterable[Tuple[int, int]]:
        for relative_row, relative_column in chain(permutations(range(-1, 2, 1), 2), ((1, 1), (-1, -1))):
            if self._is_inside(x := row + relative_row, y := column + relative_column):
                yield x, y

    def _spread_empty(self, row: int, column: int) -> Tuple[Tuple[int, int], ...]:
        if (row, column) in self._revealed or not self._is_inside(row, column):
            return ()

        self._revealed.append((row, column))

        if self._board[row][column] == 0:
            # This generate 8 tuples that represent the relative distance from the position with its adjacent positions.
            # (-1, -1), (-1, 0), (-1, 1)...
            gen = cast(Iterable[Tuple[int, int]], chain(permutations(range(-1, 2, 1), 2), ((1, 1), (-1, -1))))
            return (
                (row, column),
                *tuple(cpl for dx, dy in gen for cpl in self._spread_empty(row + dx, column + dy)),
            )

        else:
            return ((row, column),)

    def _create_board(self, initial_play: Tuple[int, int] | None) -> BoardT:
        board: BoardT = [[0 for _ in range(self._size[1])] for _ in range(self._size[0])]

        def increment_around(x: int, y: int):
            """Increment the value of the cells around the given position."""

            # I think this can be done in a more elegant way
            def incr(x: int, y: int):
                if 0 <= x < self._size[0] and 0 <= y < self._size[1] and board[x][y] != -1:
                    board[x][y] += 1

            relative_positions: Iterable[Tuple[int, int]] = cast(
                Iterable[Tuple[int, int]], chain(permutations(range(-1, 2, 1), 2), ((1, 1), (-1, -1)))
            )
            for dx, dy in relative_positions:
                incr(x + dx, y + dy)

        positions_couples = {(x, y) for x in range(self._size[0]) for y in range(self._size[1])}
        if initial_play is not None:
            positions_couples -= {initial_play}

        mines_pos = self._random.sample(list(positions_couples), self._mines_nb)
        for x, y in mines_pos:
            board[x][y] = -1
            increment_around(x, y)

        return board

    def undo(self):
        """Cancel the last move if it was a bomb hit."""
        if not self.game_over:
            return

        last_play = self._history.pop()
        self._revealed.remove(last_play.positions[0])

    def restart(self) -> Self:
        """Restart a game, but with the same mines positions.

        Alter the object in-place.
        """
        self._revealed = []
        self._history = []
        self.flags = []

        return self
