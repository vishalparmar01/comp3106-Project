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


def iter_manhattan_radius(x: int, y: int, grid: np.ndarray[np.uint8], width: int):
    """Iterates over each valid coordinate with a manhattan distance of ``width`` of the agent."""
    for i in range(max(0, width - x), min(width, y + 1)):
        yield x - width + i, y - i
    for i in range(max(0, width - y), min(width, grid.shape[0] - x)):
        yield x + i, y - width + i
    for i in range(max(0, x + width - grid.shape[0] + 1), min(width, grid.shape[1] - y)):
        yield x + width - i, y + i
    for i in range(max(0, y + width - grid.shape[1] + 1), min(width, x + 1)):
        yield x - i, y + width - i


def iter_closest(x: int, y: int, grid: np.ndarray[np.uint8]):
    """Iterates over every valid index in spirals starting with the closest to the agent."""
    yield x, y
    for width in range(1, max(x, grid.shape[0] - x - 1) + max(y, grid.shape[1] - y - 1) + 1):
        for coords in iter_manhattan_radius(x, y, grid, width):
            yield coords


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

    def move_closer(self, other_agents: AgentMap) -> None:
        assert self.goal
        other_locations = {agent_type: agent.pos for agent_type, agent in other_agents.items()}
        if self.y < self.goal[1] and (self.x, self.y + 1) not in other_locations.values():
            self.y += 1
        elif self.y > self.goal[1] and (self.x, self.y - 1) not in other_locations.values():
            self.y -= 1
        elif self.x < self.goal[0] and (self.x + 1, self.y) not in other_locations.values():
            self.x += 1
        elif self.x > self.goal[0] and (self.x - 1, self.y) not in other_locations.values():
            self.x -= 1
        else:
            print(f"{self}: Tried to move to goal but already at goal, or could not otherwise move")
            (x, y) = self.maximize_personal_space(other_locations)
            self.x += x
            self.y += y

    def clean_up(self) -> None:
        """Sets the grid at the current index to be empty."""
        if Cell(self.grid[self.pos]) not in (Cell.WALL, Cell.BIN):
            self.grid[self.pos] = Cell.EMPTY.value

    def tick(self, other_agents: AgentMap) -> None:
        if self.pos == self.goal:
            self.clean_up()
            self.goal = None
        elif self.run_away(other_agents) or not self.goal:
            return
        else:
            self.move_closer(other_agents)

    def location(self) -> Point:
        return self.x, self.y

    @property
    def pos(self) -> Point:
        return self.x, self.y

    def find_nearest_cell(self, *cell_types: Cell) -> Point | None:
        """Returns the coordinates of the nearest cell with the given value."""
        values = tuple(cell.value for cell in cell_types)
        for coords in iter_closest(self.x, self.y, self.grid):
            if self.grid[coords] in values:
                return coords

    def movement_distance_heuristic(self, *cell_types: Cell) -> dict[Point, int]:
        distances: dict[Point, int] = {}
        values = tuple(cell.value for cell in cell_types)
        for (x, y) in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
            distances[(x, y)] = sum(self.grid.shape)
            for coords in iter_closest(self.x + x, self.y + y, self.grid):
                if self.grid[coords] in values:
                    distances[(x, y)] = manhattan_distance((self.x + x, self.y + y), coords)
                    break
        return distances


class Garbage(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.current_trash = 0
        self.trash_capacity = 5
        self.agent_type = AgentType.GARBAGE

    def __repr__(self):
        return super().__repr__() + f" ({self.current_trash}/{self.trash_capacity})"

    def update_goal(self):
        if self.current_trash >= self.trash_capacity:
            self.goal = self.find_nearest_cell(Cell.BIN)
        else:
            self.goal = self.find_nearest_cell(Cell.WETTRASH, Cell.DRYTRASH) or self.find_nearest_cell(Cell.BIN)

    def tick(self, other_agents: AgentMap) -> None:
        if not self.goal:
            self.update_goal()
        super().tick(other_agents)

    def clean_up(self) -> None:
        if self.grid[self.pos] == Cell.BIN.value:
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
