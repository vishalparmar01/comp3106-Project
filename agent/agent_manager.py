from abc import ABC
from enum import Enum
from typing import List, Tuple
import numpy as np


class AgentType(Enum):
    GARBAGE = 1
    MOP = 2
    VACUUM = 3


Point = tuple[int, int]
AgentLocations = dict[AgentType: Point]


class AgentManager(ABC):
    """API for interacting with a group of agents."""

    def __init__(self, grid: np.ndarray, locations: AgentLocations):
        """Environment and initial agent locations"""
        self.grid = grid

    def tick(self) -> None:
        """One timestep. Updates grid and agent locations."""

    def agent_locations(self) -> AgentLocations:
        """Returns (x, y) location of each agent."""

    def set_agent_actions(self, agent_type: AgentType, actions: List[str]) -> None:
        """Set actions for a specific agent."""

    def __repr__(self) -> str:
        """Representation of agents"""
