from abc import ABC
from enum import Enum

import numpy as np


class AgentType(Enum):
    GARBAGE = 1
    MOP = 2
    VACUUM = 3


class AgentManager(ABC):
    """API for interacting with a group of agents."""

    def __init__(self, grid: np.ndarray):
        self.grid = grid

    def tick(self) -> None:
        """One timestep. Updates grid and agent locations."""

    def agent_locations(self) -> dict[AgentType: tuple[int, int]]:
        """Returns (x, y) location of each agent."""

    def __repr__(self) -> str:
        """Representation of agents"""
