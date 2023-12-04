from enum import Enum
from random import choice, randint

import numpy as np

from agent.agent_manager import AgentType, AgentLocations


class Cell(Enum):
    EMPTY = 0
    WETTRASH = 1
    DRYTRASH = 2
    DUSTY = 3
    SOAKED = 6
    BIN = 4
    WALL = 5


def create_dynamic_grid(rows: int, columns: int):
    # Create a dynamic grid with the specified number of rows and columns
    grid = np.zeros((rows, columns), dtype=np.uint8)

    bin_placed = False
    total_cells = rows * columns
    min_target_cells = total_cells * 0.65 # At least 1/2 of the grid should have trash
    max_target_cells = total_cells * 0.75  # 3/4 or less of the grid should have trash

    target_cells = randint(min_target_cells, max_target_cells)
    print(target_cells)
    trash_cells = 0

    for i in range(rows):
        for j in range(columns):
            if trash_cells < target_cells and randint(0, 1):  # Randomly choose whether to place trash
                trash_type = choice([Cell.WETTRASH, Cell.DRYTRASH, Cell.DUSTY, Cell.SOAKED]).value
                grid[i, j] = trash_type
                trash_cells += 1
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
