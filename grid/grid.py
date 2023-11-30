from enum import Enum
from random import choice, randint

import numpy as np

from agent.agent_manager import AgentType, AgentLocations


class Cell(Enum):
    EMPTY = 0
    WETTRASH = 1
    DRYTRASH = 2
    DUSTY = 3
    BIN = 4
    WALL = 5


def create_dynamic_grid(rows: int, columns: int):
    # Create a dynamic grid with the specified number of rows and columns
    grid = np.zeros((rows, columns), dtype=np.uint8)

    bin_placed = False
    for i in range(rows):
        for j in range(columns):
            if randint(0, 1):  # Randomly choose whether to place wet or trash
                grid[i, j] = choice([Cell.WETTRASH, Cell.DRYTRASH]).value  # Indicate the presence of an element in the grid
            elif not bin_placed:
                grid[i, j] = Cell.BIN.value
                bin_placed = True

    if not bin_placed:
        grid[0, 0] = Cell.BIN.value

    return grid


def print_grid(grid):
    # Print the grid
    for row in grid:
        print(" ".join(map(str, row)))


def get_start_positions(grid: np.ndarray) -> AgentLocations:
    return {
        AgentType.GARBAGE: (0, 0),
        AgentType.VACUUM: (1, 0),
        AgentType.MOP: (2, 0),
    }


# Example usage
# rows = int(input("Enter the number of rows: "))
# columns = int(input("Enter the number of columns: "))

# grid = create_dynamic_grid(rows, columns)
#print("\nInitial Grid:")
#print_grid(grid)
