import numpy as np

from agent.agent_manager import AgentManager, AgentType
from grid.grid import Cell


class Agent:
    def __init__(self, grid: np.ndarray, x: int, y: int):
        self.grid = grid
        self.x = x
        self.y = y

    def tick(self, other_agents: dict[AgentType: tuple[int, int]]) -> None:
        # Temp testing behaviour: clean current square if dirty, move down if not
        if self.grid[self.x, self.y]:
            self.grid[self.x, self.y] = Cell.EMPTY.value
        else:
            self.y += 1

    def location(self) -> tuple[int, int]:
        return self.x, self.y

    def __str__(self) -> str:
        return f"{str(self.__class__).split('.')[-1][:-2]} at ({self.x}, {self.y})"


class Garbage(Agent):
    ...


class Vacuum(Agent):
    ...


class Mop(Agent):
    ...


class SeparateAgents(AgentManager):
    def __init__(self, grid: np.ndarray):
        super().__init__(grid)
        self.agents = {
            AgentType.GARBAGE: Garbage(self.grid, 0, 0),
            AgentType.VACUUM: Vacuum(self.grid, 1, 0),
            AgentType.MOP: Mop(self.grid, 2, 0),
        }

    def tick(self) -> None:
        for agent in self.agents.values():
            agent.tick(self.agents)

    def agent_locations(self) -> dict[AgentType: tuple[int, int]]:
        return {agent_type: agent.location() for (agent_type, agent) in self.agents.items()}

    def __repr__(self) -> str:
        return "Separately: " + ", ".join(map(str, self.agents.values()))
