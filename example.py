from minesweeper import GameState, Minesweeper

game = Minesweeper((10, 10), 10)


def display() -> None:
    print("   ", *range(game.size[0]))
    print("   ", *("|" * game.size[0]))
    for x, int in enumerate(game.board):
        special_repr = {
            -1: "X",
            0: " ",
        }
        print(x, "— ", end="")
        print(
            *(
                special_repr.get(case, case) if (x, y) in game.revealed else ("F" if (x, y) in game.flags else "■")
                for y, case in enumerate(int)
            ),
            sep=" ",
        )


def init():
    init = input("Where do you want to play ? 'column,row'\n")
    column, row = tuple(int(x) for x in init.split(","))
    game.new((row, column))


display()
init()
while True:
    display()
    if game.game_over:
        print("Game Over !")
        if game.state == GameState.LOST:
            print("You lost!")
        else:
            print("You won!")
        match input("What next ? u for undo, n for new\n"):
            case "n":
                init()
            case "u":
                game.undo()
            case _:
                print("Invalid response, new game created.")
                init()
        display()
    r = input("Where do you want to play ? e.g. '0,0' or 'f0,0' for flag.\n")
    column, row = r.split(",")
    if flag := column.startswith("f"):
        game.toggle_flag(int(row), int(column[1:]))
    else:
        game.play(int(row), int(column))
