from queue import PriorityQueue
from typing import List, Tuple
from enum import Enum
import numpy as np
from agent.agent_manager import AgentType, AgentManager, AgentLocations
from grid.grid import Cell


class Action(Enum):
    MOVE_UP = "UP"
    MOVE_DOWN = "DOWN"
    MOVE_LEFT = "LEFT"
    MOVE_RIGHT = "RIGHT"


class AStarController(AgentManager):
    def __init__(self, grid: np.ndarray, locations: AgentLocations):
        super().__init__(grid, locations)
        self.agent_positions = locations

    def agent_locations(self) -> dict[AgentType: tuple[int, int]]:
        return self.agent_positions

    def __str__(self) -> str:
        return "A* Controller with agents at: " + str(self.agent_positions)

    def a_star(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Action]:
        def heuristic(current, goal):
            return abs(current[0] - goal[0]) + abs(current[1] - goal[1])

        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {}
        g_score = {start: 0}

        path = []  # List to store the actions

        while not open_set.empty():
            current_cost, current_node = open_set.get()

            if current_node == goal:
                # If a cleaning action is pending, add it to the path
                if self.grid[current_node[0], current_node[1]] == Cell.DRYTRASH.value:
                    self.grid[current_node[0], current_node[1]] = Cell.EMPTY.value
                while current_node in came_from:
                    path.append(came_from[current_node])
                    current_node = came_from[current_node]
                return path[::-1]

            # Check if the current node needs cleaning
            if self.grid[current_node[0], current_node[1]] == Cell.DRYTRASH.value:
                self.grid[current_node[0], current_node[1]] = Cell.EMPTY.value
                continue

            for action in Action:
                new_node = self.apply_action(current_node, action)
                if self.is_valid_move(new_node) and new_node not in g_score:
                    g_score[new_node] = g_score[current_node] + 1
                    f_score = g_score[new_node] + heuristic(new_node, goal)
                    open_set.put((f_score, new_node))
                    came_from[new_node] = action

        return path  # Return the list of actions

    def apply_action(self, node: Tuple[int, int], action: Action) -> Tuple[int, int]:
        x, y = node
        if action == Action.MOVE_UP:
            return x, y - 1
        elif action == Action.MOVE_DOWN:
            return x, y + 1
        elif action == Action.MOVE_LEFT:
            return x - 1, y
        elif action == Action.MOVE_RIGHT:
            return x + 1, y
        return x, y

    def is_valid_move(self, node: Tuple[int, int]) -> bool:
        x, y = node
        return 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]) and self.grid[x, y] != Cell.WALL.value

    def tick(self) -> None:
        garbage_start = self.agent_positions[AgentType.GARBAGE]
        vacuum_start = self.agent_positions[AgentType.VACUUM]
        mop_start = self.agent_positions[AgentType.MOP]

        garbage_goal = self.find_closest_goal(garbage_start, Cell.DRYTRASH)
        vacuum_goal = self.find_closest_goal(vacuum_start, Cell.DUSTY)
        mop_goal = self.find_closest_goal(mop_start, Cell.WETTRASH)

        garbage_actions = self.a_star(garbage_start, garbage_goal)
        vacuum_actions = self.a_star(vacuum_start, vacuum_goal)
        mop_actions = self.a_star(mop_start, mop_goal)

        agent_actions = {
            AgentType.GARBAGE: garbage_actions,
            AgentType.VACUUM: vacuum_actions,
            AgentType.MOP: mop_actions
        }

        for agent_type, actions in agent_actions.items():
            self.tick_agent(agent_type, actions)

    def tick_agent(self, agent_type: AgentType, actions: List[Action]) -> None:
        for action in actions:
            current_position = self.agent_positions[agent_type]

            # Update the visual grid based on the actions
            if action == Action.MOVE_UP or action == Action.MOVE_DOWN or \
                action == Action.MOVE_LEFT or action == Action.MOVE_RIGHT:
                # Update agent positions if it's a movement action
                new_position = self.apply_action(current_position, action)
                print(f"{agent_type.name} moved from {current_position} to {new_position}")
                self.agent_positions[agent_type] = new_position

            # Check if the current node needs cleaning
            if self.grid[current_position[0], current_position[1]] == Cell.DRYTRASH.value:
                self.grid[current_position[0], current_position[1]] = Cell.EMPTY.value
                print(f"{agent_type.name} cleaned cell at {current_position}")

        # Set the cell value to EMPTY at the final position
        final_position = self.agent_positions[agent_type]
        self.grid[final_position[0], final_position[1]] = Cell.EMPTY.value

    def find_closest_goal(self, start: Tuple[int, int], goal_type: Cell) -> Tuple[int, int]:
        def heuristic(current, goal):
            return abs(current[0] - goal[0]) + abs(current[1] - goal[1])

        def is_goal(node):
            x, y = node
            return self.grid[x, y] == goal_type.value

        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {}

        while not open_set.empty():
            current_cost, current_node = open_set.get()

            if is_goal(current_node):
                return current_node

            for action in Action:
                new_node = self.apply_action(current_node, action)
                if self.is_valid_move(new_node) and new_node not in came_from:
                    g_score = current_cost + 1
                    f_score = g_score + heuristic(new_node, start)
                    open_set.put((f_score, new_node))
                    came_from[new_node] = current_node

        return start  # No goal found, return the original start position

