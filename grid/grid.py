from enum import Enum
from random import choice, random, sample

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


def create_dynamic_grid(rows: int, columns: int, fill: float, garbage: float, bins: int):
    """Create a dynamic grid with the specified number of rows and columns"""
    assert bins < rows * columns
    grid = np.zeros((rows, columns), dtype=np.uint8)

    for i in range(rows):
        for j in range(columns):
            if random() < fill:  # Randomly choose whether to place trash
                grid[i, j] = choice(
                    [Cell.WETTRASH, Cell.DRYTRASH]
                    if random() < garbage else
                    [Cell.DUSTY, Cell.SOAKED]
                ).value

    empty = np.argwhere(grid == 0)
    bin_indices = np.array(sample(list(empty), min(len(empty), bins)))
    if len(empty) < bins:
        more_indices = np.array(sample(list(np.argwhere(grid)), bins - len(empty)))
        if len(empty):
            bin_indices = np.concatenate((bin_indices, more_indices))
        else:
            bin_indices = more_indices
    grid[bin_indices[:, 0], bin_indices[:, 1]] = Cell.BIN.value

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
