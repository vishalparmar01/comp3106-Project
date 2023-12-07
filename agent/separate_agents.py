from random import choice
from typing import Any, Generator, Callable

import numpy as np
import shapely

from agent.agent_manager import AgentLocations, AgentManager, AgentType, Point
from grid.grid import Cell
from sim.print import print


AgentMap = dict[AgentType, "Agent"]


def manhattan_distance(p1: Point, p2: Point) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def agent_distances(locations: AgentMap, agent: AgentType, test_pos: Point = None) -> dict[AgentType, float]:
    return {
        other_type: manhattan_distance(
            test_pos or locations[agent].pos, other_agent.pos
        ) - max(
            locations[agent].priority - other_agent.priority, 0
        ) / 2
        for other_type, other_agent in locations.items()
        if other_type != agent
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


MoveHeuristic = dict[Point, int | float]


def best_keys(heuristic: MoveHeuristic, metric: Callable[..., int]) -> set[Point]:
    best_value = metric(heuristic.values())
    return {point for point, h in heuristic.items() if h == best_value}


def best_key(heuristic: MoveHeuristic, metric: Callable[..., int]) -> Point:
    return random_take(best_keys(heuristic, metric))


def random_take(s: set[Point]) -> Point:
    return choice(list(s))


TARGETS = {Cell.BIN, Cell.DRYTRASH, Cell.DUSTY, Cell.WETTRASH, Cell.SOAKED}


class Agent:
    agent_type: AgentType
    cell_types: tuple[Cell, ...]

    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        self.grid = grid
        self.x = x
        self.y = y
        self.goal: Point | None = None

    def __repr__(self):
        return f"{type(self).__name__} at {self.pos}"

    def run_away(self, other_agents: AgentMap) -> bool:
        """Returns whether the agent had to get out of the way of other agents with higher priority."""
        # print(self)
        # print(vars(self))
        # print(other_agents)
        if self.goal is None:
            personal_movements = self.personal_space_heuristic(other_agents)
            nearest_target = self.find_nearest_cell(*(TARGETS - set(self.cell_types)))
            target_movements = self.manhattan_distance_heuristic(nearest_target) if nearest_target else None
            if max(personal_movements.values()) > 6:
                if not nearest_target or manhattan_distance(self.pos, nearest_target) > 6:
                    return False
                personal_movements = target_movements
            best_personal = best_keys(personal_movements, max)
            (x, y) = best_key({move: value for move, value in target_movements.items() if move in best_personal}, max)
            self.x += x
            self.y += y
            return True
        return False

    def move_closer(self, other_agents: AgentMap) -> Point:
        assert self.goal
        personal_space = self.personal_space_heuristic(other_agents)
        closer_moves = self.manhattan_distance_heuristic(self.goal)
        if min(personal_space.values()) > 0:
            best_moves = best_keys(closer_moves, min)
            return best_key({move: h for move, h in personal_space.items() if move in best_moves}, max)
        else:
            best_moves = best_keys(personal_space, max)
            closest_trash = self.type_distance_heuristic(*self.cell_types)
            move_distances = {
                point: manhattan_distance((point[0] + self.x, point[1] + self.y), trash)
                for point, trash in closest_trash.items()
                if point in best_moves
            }
            key = best_key(move_distances, min)
            self.goal = None
            if len(best_moves) == 1:
                return random_take(best_moves)
            return key

    def clean_up(self) -> None:
        """Sets the grid at the current index to be empty."""
        if Cell(self.grid[self.pos]) not in (Cell.WALL, Cell.BIN):
            self.grid[self.pos] = Cell.EMPTY.value

    def tick(self, other_agents: AgentMap) -> None:
        # print(self)
        self.goal = self.goal or self.find_best_cell(*self.cell_types)
        if self.run_away(other_agents) or not self.goal:
            return
        else:
            (x, y) = self.move_closer(other_agents)
            self.x += x
            self.y += y
        if self.pos == self.goal:
            self.clean_up()
            self.goal = None

    @property
    def priority(self):
        return 1 if self.goal else 0

    @property
    def pos(self) -> Point:
        return self.x, self.y

    def valid_moves(self) -> Generator[Point, Any, None]:
        for (x, y) in [(0, 0), (-1, 0), (0, -1), (1, 0), (0, 1)]:
            if 0 <= self.x + x < self.grid.shape[0] and 0 <= self.y + y < self.grid.shape[1]:
                yield x, y

    def find_nearest_cell(self, *cell_types: Cell) -> Point | None:
        """Returns the coordinates of the nearest cell with the given value."""
        values = tuple(cell.value for cell in cell_types)
        for coords in iter_closest(self.x, self.y, self.grid):
            if self.grid[coords] in values:
                return coords

    def find_best_cell(self, *cell_types: Cell) -> Point | None:
        """Returns the coordinates of the best cell with the given value."""
        if not any(cell.value in self.grid for cell in cell_types):
            return None
        if Cell(self.grid[self.pos]) in cell_types:
            return self.pos
        hull_distance = self.convex_hull_grid_heuristic(*cell_types)
        grid_distance = self.grid_distance_heuristic()
        combined = (hull_distance + 1) * + grid_distance
        combined[~self.grid_cell_mask(*cell_types)] = np.float64('inf')
        best = np.argmin(combined)
        best_index = np.unravel_index(best, self.grid.shape)
        return int(best_index[0]), int(best_index[1])

    def personal_space_heuristic(self, other_agents: AgentMap) -> MoveHeuristic:
        distances: MoveHeuristic = {}
        for (x, y) in self.valid_moves():
            distances[(x, y)] = min(
                agent_distances(
                    other_agents,
                    self.agent_type,
                    (self.x + x, self.y + y)
                ).values()
            )
        return distances

    def type_distance_heuristic(self, *cell_types: Cell) -> dict[Point, Point]:
        distances: dict[Point, Point] = {}
        values = tuple(cell.value for cell in cell_types)
        for (x, y) in self.valid_moves():
            for coords in iter_closest(self.x + x, self.y + y, self.grid):
                if self.grid[coords] in values:
                    distances[(x, y)] = coords
                    break
        return distances

    def manhattan_distance_heuristic(self, cell: Point) -> MoveHeuristic:
        distances: MoveHeuristic = {}
        for (x, y) in self.valid_moves():
            distances[(x, y)] = manhattan_distance((self.x + x, self.y + y), cell)
        return distances

    def grid_cell_mask(self, *cell_types: Cell) -> np.ndarray[np.bool_]:
        mask = np.zeros(self.grid.shape, dtype=np.bool_)
        for cell_type in cell_types:
            mask |= self.grid == cell_type.value
        return mask

    def convex_hull_grid_heuristic(self, *cell_types: Cell) -> np.ndarray[np.float64]:
        mask = self.grid_cell_mask(*cell_types)
        indices = np.array(mask.nonzero()).T
        if len(indices) < 2:
            return np.zeros(self.grid.shape)
        hull: shapely.Polygon = shapely.convex_hull(shapely.MultiPoint(indices))
        boundary: shapely.LineString = hull.boundary
        distance_func = np.frompyfunc(lambda x, y: boundary.distance(shapely.Point(x, y)), 2, 1)
        return np.fromfunction(distance_func, self.grid.shape, dtype=np.float64)

    def grid_distance_heuristic(self) -> np.ndarray[np.float64]:
        return np.fromfunction(lambda x, y: np.abs(x - self.x) + np.abs(y - self.y), self.grid.shape, dtype=np.int64)


class Garbage(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int, capacity: int = 10):
        super().__init__(grid, x, y)
        self.current_trash = 0
        self.trash_capacity = capacity
        self.agent_type = AgentType.GARBAGE
        self.cell_types = (Cell.WETTRASH, Cell.DRYTRASH)

    def __repr__(self):
        trash = f"{self.current_trash}/{self.trash_capacity}"
        searching = ','.join(cell.name for cell in self.cell_types)
        return super().__repr__() + f" ({trash}, {searching})"

    def tick(self, other_agents: AgentMap) -> None:
        if Cell.WETTRASH.value not in self.grid and Cell.DRYTRASH.value not in self.grid and self.current_trash:
            self.cell_types = (Cell.BIN,)
        super().tick(other_agents)

    @property
    def priority(self) -> int:
        return int(self.current_trash == self.trash_capacity) + 1

    def clean_up(self) -> None:
        if self.grid[self.pos] == Cell.BIN.value:
            self.current_trash = 0
            self.cell_types = (Cell.WETTRASH, Cell.DRYTRASH)
        elif Cell(self.grid[self.pos]) in (Cell.WETTRASH, Cell.DRYTRASH):
            self.current_trash += 1
            if self.current_trash == self.trash_capacity:
                self.cell_types = (Cell.BIN,)
            elif self.current_trash > self.trash_capacity:
                print(f"Garbage overflow {self.current_trash}")
            if self.grid[self.pos] == Cell.WETTRASH.value:
                self.grid[self.pos] = Cell.SOAKED.value
            else:
                self.grid[self.pos] = Cell.DUSTY.value

    def run_away(self, other_agents: AgentMap) -> bool:
        distances = agent_distances(other_agents, AgentType.GARBAGE)
        if self.current_trash == self.trash_capacity and min(distances.values()) >= 2:
            return False
        return super().run_away(other_agents)

    def find_best_cell(self, *cell_types: Cell) -> Point | None:
        if Cell.BIN in cell_types:
            return self.find_nearest_cell(Cell.BIN)
        return super().find_best_cell(*cell_types)


class Vacuum(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.agent_type = AgentType.VACUUM
        self.cell_types = (Cell.DUSTY,)


class Mop(Agent):
    def __init__(self, grid: np.ndarray[np.uint8], x: int, y: int):
        super().__init__(grid, x, y)
        self.agent_type = AgentType.MOP
        self.cell_types = (Cell.SOAKED,)


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
        return {agent_type: agent.pos for (agent_type, agent) in self.agents.items()}

    def finished(self) -> bool:
        for agent in self.agents.values():
            if agent.goal is not None or isinstance(agent, Garbage) and agent.current_trash > 0:
                return False
        return True

    def __repr__(self) -> str:
        return "Separately: " + ", ".join(map(str, self.agents.values()))
