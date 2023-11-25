from enum import Enum
from random import choice, randint

import numpy as np


class Cell(Enum):
    EMPTY = 0
    WET = 1
    DRY = 2
    DIRTY = 3
    BIN = 4
    WALL = 5


def create_dynamic_grid(rows: int, columns: int):
    # Create a dynamic grid with the specified number of rows and columns
    grid = np.zeros((rows, columns), dtype=np.uint8)

    for i in range(rows):
        for j in range(columns):
            if randint(0, 1):  # Randomly choose whether to place wet or trash
                grid[i, j] = choice([Cell.WET, Cell.DRY]).value  # Indicate the presence of an element in the grid

    return grid


def print_grid(grid):
    # Print the grid
    for row in grid:
        print(" ".join(map(str, row)))


# Example usage
# rows = int(input("Enter the number of rows: "))
# columns = int(input("Enter the number of columns: "))

# grid = create_dynamic_grid(rows, columns)
#print("\nInitial Grid:")
#print_grid(grid)
