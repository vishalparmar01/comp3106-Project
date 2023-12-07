from abc import ABC
from enum import Enum
from random import choice
from typing import List

import numpy as np

from grid.grid import Cell


class AgentType(Enum):
    GARBAGE = 1
    MOP = 2
    VACUUM = 3


Point = tuple[int, int]
AgentLocations = dict[AgentType, Point]

AGENT_TARGETS = {
    AgentType.GARBAGE: (Cell.BIN, Cell.DRYTRASH, Cell.WETTRASH),
    AgentType.MOP: (Cell.SOAKED,),
    AgentType.VACUUM: (Cell.DUSTY,),
}


def get_start_positions(grid: np.ndarray, randomise: bool) -> AgentLocations:
    if randomise:
        return {
            AgentType.GARBAGE: tuple(choice(np.argwhere(grid == Cell.BIN.value))),
            AgentType.VACUUM: tuple(choice(np.argwhere(grid == Cell.SOAKED.value))),
            AgentType.MOP: tuple(choice(np.argwhere(grid == Cell.DUSTY.value))),
        }
    return {
        AgentType.GARBAGE: (0, 0),
        AgentType.VACUUM: (1, 0),
        AgentType.MOP: (2, 0),
    }


class AgentManager(ABC):
    """API for interacting with a group of agents."""

    def __init__(self, grid: np.ndarray, locations: AgentLocations, garbage_capacity: int):
        """Environment and initial agent locations."""
        self.grid = grid

    def tick(self) -> None:
        """One timestep. Updates grid and agent locations."""

    def agent_locations(self) -> AgentLocations:
        """Returns (x, y) location of each agent."""

    def set_agent_actions(self, agent_type: AgentType, actions: List[str]) -> None:
        """Set actions for a specific agent."""

    def finished(self) -> bool:
        """Whether the agents are finished moving."""

    def __repr__(self) -> str:
        """Representation of agents."""
