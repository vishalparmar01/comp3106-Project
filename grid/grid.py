from enum import Enum
from random import choice, random

import numpy as np

from agent.agent_manager import AgentType, AgentLocations


class Cell(Enum):
    EMPTY = 0
    WETTRASH = 1
    SOAKED = 6
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
            if random() < 0.65:  # Randomly choose whether to place trash
                grid[i, j] = choice([Cell.WETTRASH, Cell.DRYTRASH, Cell.DUSTY, Cell.SOAKED]).value
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
