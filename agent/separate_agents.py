import numpy as np

from agent.agent_manager import AgentLocations, AgentManager, AgentType, Point
from grid.grid import Cell
from sim.print import print


AgentMap = dict[AgentType, "Agent"]


def manhattan_distance(x: Point, y: Point) -> int:
    return abs(x[0] - y[0]) + abs(x[1] - y[1])


def agent_distances(locations: AgentLocations, agent: AgentType) -> dict[AgentType, int]:
    return {
        other_agent: manhattan_distance(locations[agent], other_point)
        for other_agent, other_point in locations.items()
        if other_agent != agent
    }


class Agent:
    agent_type: AgentType

    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        self.grid = grid
        self.x = x
        self.y = y
        self.goal: Point | None = None

    def __repr__(self):
        return f"{type(self).__name__} at {self.pos}"

    def maximize_personal_space(self, other_locations: AgentLocations) -> Point:
        distances = agent_distances(other_locations, self.agent_type)
        best_movement = (0, 0)
        best_min = min(distances.values())
        for (x, y) in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if 0 <= self.x + x < self.grid.shape[0] and 0 <= self.y + y < self.grid.shape[1]:
                closest_agent = min(
                    agent_distances(
                        {
                            **other_locations,
                            self.agent_type: (self.x + x, self.y + y)
                        },
                        self.agent_type
                    ).values()
                )
                if closest_agent > best_min:
                    best_min = closest_agent
                    best_movement = (x, y)
        return best_movement

    def run_away(self, other_agents: AgentMap) -> bool:
        """Returns whether the agent had to get out of the way of other agents with higher priority."""
        other_locations: AgentLocations = {agent_type: agent.pos for agent_type, agent in other_agents.items()}
        if self.goal is None:
            (x, y) = self.maximize_personal_space(other_locations)
            self.x += x
            self.y += y
            return True
        return False

    def move_closer(self) -> None:
        assert self.goal
        if self.y < self.goal[1]:
            self.y += 1
        elif self.y > self.goal[1]:
            self.y -= 1
        elif self.x < self.goal[0]:
            self.x += 1
        elif self.x > self.goal[0]:
            self.x -= 1
        else:
            print(f"{self}: Tried to move to goal but already at goal")

    def clean_up(self) -> None:
        """Sets the grid at the current index to be empty."""
        if Cell(self.grid[self.pos]) not in (Cell.WALL, Cell.BIN):
            self.grid[self.pos] = Cell.EMPTY.value

    def tick(self, other_agents: AgentMap) -> None:
        print(self, self.goal)
        if self.run_away(other_agents) or not self.goal:
            return
        if self.pos == self.goal:
            self.clean_up()
            self.goal = None
        else:
            self.move_closer()

    def location(self) -> Point:
        return self.x, self.y

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
        for width in range(1, max(self.x, self.grid.shape[0] - self.x - 1) + max(self.y, self.grid.shape[1] - self.y - 1) + 1):
            for coords in self.iter_manhattan_radius(width):
                yield coords

    def find_nearest_cell(self, *cell_types: Cell) -> Point | None:
        """Returns the coordinates of the nearest cell with the given value."""
        values = tuple(cell.value for cell in cell_types)
        for coords in self.iter_closest():
            if self.grid[coords] in values:
                return coords

    def movement_heuristics(self, other_locations: AgentLocations) -> dict[Point, int]:
        ...


class Garbage(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.bin = self.find_bin()
        self.current_trash = 0
        self.trash_capacity = 5
        self.agent_type = AgentType.GARBAGE

    def __repr__(self):
        return super().__repr__() + f" ({self.current_trash}/{self.trash_capacity})"

    def update_goal(self):
        if self.current_trash >= self.trash_capacity:
            self.goal = self.bin
        else:
            self.goal = self.find_nearest_cell(Cell.WETTRASH, Cell.DRYTRASH) or self.bin

    def tick(self, other_agents: AgentMap) -> None:
        if not self.goal:
            self.update_goal()
        super().tick(other_agents)

    def find_bin(self) -> Point:
        for i in range(self.grid.shape[0]):
            for j in range(self.grid.shape[1]):
                if self.grid[i, j] == Cell.BIN.value:
                    return i, j
        raise Exception("Could not find bin")

    def clean_up(self) -> None:
        if self.pos == self.bin:
            self.current_trash = 0
        elif Cell(self.grid[self.pos]) in (Cell.WETTRASH, Cell.DRYTRASH):
            self.current_trash += 1
            if self.current_trash > self.trash_capacity:
                print(f"Garbage overflow {self.current_trash}")
            if self.grid[self.pos] == Cell.WETTRASH.value:
                self.grid[self.pos] = Cell.SOAKED.value
            else:
                self.grid[self.pos] = Cell.DUSTY.value

    def run_away(self, other_agents: AgentMap) -> bool:
        other_locations: AgentLocations = {agent_type: agent.pos for agent_type, agent in other_agents.items()}
        distances = agent_distances(other_locations, AgentType.GARBAGE)
        if self.current_trash == self.trash_capacity and min(distances.values()) >= 2:
            return False
        return super().run_away(other_agents)


class Vacuum(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.agent_type = AgentType.VACUUM

    def tick(self, other_agents: AgentMap) -> None:
        self.goal = self.goal or self.find_nearest_cell(Cell.DUSTY)
        super().tick(other_agents)


class Mop(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.agent_type = AgentType.MOP

    def tick(self, other_agents: AgentMap) -> None:
        self.goal = self.goal or self.find_nearest_cell(Cell.SOAKED)
        super().tick(other_agents)


CLASS_MAP = {
    AgentType.GARBAGE: Garbage,
    AgentType.VACUUM: Vacuum,
    AgentType.MOP: Mop,
}


class SeparateAgents(AgentManager):
    def __init__(self, grid: np.ndarray, locations: AgentLocations):
        super().__init__(grid, locations)
        self.agents: AgentMap = {agent: CLASS_MAP[agent](grid, x, y) for agent, (x, y) in locations.items()}

    def tick(self) -> None:
        for agent in self.agents.values():
            agent.tick(self.agents)

    def agent_locations(self) -> AgentLocations:
        return {agent_type: agent.location() for (agent_type, agent) in self.agents.items()}

    def finished(self) -> bool:
        for agent in self.agents.values():
            if agent.goal is not None or isinstance(agent, Garbage) and agent.current_trash > 0:
                return False
        return True

    def __repr__(self) -> str:
        return "Separately: " + ", ".join(map(str, self.agents.values()))
