import numpy as np

from agent.agent_manager import AgentLocations, AgentManager, AgentType, LoggerFunction, Point
from grid.grid import Cell


def manhattan_distance(x: Point, y: Point) -> int:
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


class Agent:
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int, log: LoggerFunction):
        self.grid = grid
        self.x = x
        self.y = y
        self.log = log
        self.goal: Point | None = None

    def run_away(self, other_agents: AgentLocations) -> bool:
        """Returns whether the agent had to get out of the way of other agents with higher priority."""
        return False

    def move_closer(self) -> None:
        if self.y < self.goal[1]:
            self.y += 1
        elif self.y > self.goal[1]:
            self.y -= 1
        elif self.x < self.goal[0]:
            self.x += 1
        elif self.x > self.goal[0]:
            self.x -= 1
        else:
            self.log(f"{self}: Tried to move to goal but already at goal")

    def clean_up(self) -> None:
        """Sets the grid at the current index to be empty."""
        if Cell(self.grid[self.pos]) not in (Cell.WALL, Cell.BIN):
            self.grid[self.pos] = Cell.EMPTY.value

    def tick(self, other_agents: AgentLocations) -> None:
        if self.run_away(other_agents) or not self.goal:
            return
        if self.pos == self.goal:
            self.clean_up()
            self.goal = None
        else:
            self.move_closer()

    def location(self) -> Point:
        return self.x, self.y

    def __str__(self) -> str:
        return f"{str(self.__class__).split('.')[-1][:-2]} at ({self.x}, {self.y})"

    @property
    def pos(self) -> Point:
        return self.x, self.y

    def iter_manhattan_radius(self, width: int):
        """Iterates over each valid coordinate with a manhattan distance of ``width`` of the agent."""
        for i in range(max(0, width - self.x), min(width, self.y + 1)):
            yield self.x - width + i, self.y - i
        for i in range(max(0, width - self.y), min(width, self.grid.shape[0] - self.x)):
            yield self.x + i, self.y - width + i
        for i in range(max(0, self.x + width - self.grid.shape[0] + 1), min(width, self.grid.shape[1] - self.y)):
            yield self.x + width - i, self.y + i
        for i in range(max(0, self.y + width - self.grid.shape[1] + 1), min(width, self.x + 1)):
            yield self.x - i, self.y + width - i

    def iter_closest(self):
        """Iterates over every valid index in spirals starting with the closest to the agent."""
        yield self.pos
        for width in range(1, max(self.x + self.y, self.grid.shape[0] - self.x + self.grid.shape[1] - self.y - 2)):
            for coords in self.iter_manhattan_radius(width):
                yield coords

    def find_nearest_cell(self, *cell_types: Cell) -> Point:
        """Returns the coordinates of the nearest cell with the given value."""
        values = tuple(cell.value for cell in cell_types)
        for coords in self.iter_closest():
            if self.grid[coords] in values:
                return coords


class Garbage(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int, log: LoggerFunction):
        super().__init__(grid, x, y, log)
        self.bin = self.find_bin()
        self.current_trash = 0
        self.trash_capacity = 5

    def tick(self, other_agents: AgentLocations) -> None:
        if not self.goal:
            if self.current_trash >= self.trash_capacity:
                self.goal = self.bin
            else:
                self.goal = self.find_nearest_cell(Cell.WETTRASH, Cell.DRYTRASH) or self.bin
        super().tick(other_agents)

    def find_bin(self) -> Point:
        for i in range(self.grid.shape[0]):
            for j in range(self.grid.shape[1]):
                if self.grid[i, j] == Cell.BIN.value:
                    return i, j

    def clean_up(self) -> None:
        if self.pos == self.bin:
            self.current_trash = 0
        elif Cell(self.grid[self.pos]) in (Cell.WETTRASH, Cell.DRYTRASH):
            self.current_trash += 1
            if self.current_trash > self.trash_capacity:
                self.log(f"Garbage overflow {self.current_trash}")
            if self.grid[self.pos] == Cell.WETTRASH.value:
                self.grid[self.pos] = Cell.SOAKED.value
            else:
                self.grid[self.pos] = Cell.DUSTY.value


class Vacuum(Agent):
    def tick(self, other_agents: AgentLocations) -> None:
        self.goal = self.goal or self.find_nearest_cell(Cell.DUSTY)
        super().tick(other_agents)


class Mop(Agent):
    def tick(self, other_agents: AgentLocations) -> None:
        self.goal = self.goal or self.find_nearest_cell(Cell.SOAKED)
        super().tick(other_agents)


CLASS_MAP = {
    AgentType.GARBAGE: Garbage,
    AgentType.VACUUM: Vacuum,
    AgentType.MOP: Mop,
}


class SeparateAgents(AgentManager):
    def __init__(self, grid: np.ndarray, locations: AgentLocations, log: LoggerFunction):
        super().__init__(grid, locations, log)
        self.agents = {agent: CLASS_MAP[agent](grid, x, y, self.log) for agent, (x, y) in locations.items()}

    def tick(self) -> None:
        for agent in self.agents.values():
            agent.tick(self.agents)

    def agent_locations(self) -> AgentLocations:
        return {agent_type: agent.location() for (agent_type, agent) in self.agents.items()}

    def __repr__(self) -> str:
        return "Separately: " + ", ".join(map(str, self.agents.values()))
