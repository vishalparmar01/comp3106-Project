import numpy as np

from agent.agent_manager import AgentLocations, AgentManager, AgentType, LoggerFunction
from grid.grid import Cell


class Agent:
    def __init__(self, grid: np.ndarray, x: int, y: int):
        self.grid = grid
        self.x = x
        self.y = y

    def tick(self, other_agents: AgentLocations) -> None:
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


CLASS_MAP = {
    AgentType.GARBAGE: Garbage,
    AgentType.VACUUM: Vacuum,
    AgentType.MOP: Mop,
}


class SeparateAgents(AgentManager):
    def __init__(self, grid: np.ndarray, locations: AgentLocations, log: LoggerFunction):
        super().__init__(grid, locations, log)
        self.agents = {agent: CLASS_MAP[agent](grid, x, y) for agent, (x, y) in locations.items()}

    def tick(self) -> None:
        for agent in self.agents.values():
            agent.tick(self.agents)

    def agent_locations(self) -> AgentLocations:
        return {agent_type: agent.location() for (agent_type, agent) in self.agents.items()}

    def __repr__(self) -> str:
        return "Separately: " + ", ".join(map(str, self.agents.values()))
