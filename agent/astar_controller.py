from enum import Enum
from queue import PriorityQueue
from typing import List, Tuple

import numpy as np

from agent.agent_manager import AgentLocations, AgentManager, AgentType
from grid.grid import Cell
from sim.print import print


class Action(Enum):
    MOVE_UP = "UP"
    MOVE_DOWN = "DOWN"
    MOVE_LEFT = "LEFT"
    MOVE_RIGHT = "RIGHT"


class AStarController(AgentManager):
    def __init__(self, grid: np.ndarray, locations: AgentLocations):
        super().__init__(grid, locations)
        self.agent_positions = locations
        self.garbage_pickup_count = 0  # Counter to track the number of trash pickups by the GARBAGE agent
        self.garbage_to_bin = False


    def agent_locations(self) -> AgentLocations:
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
                while current_node in came_from:
                    path.append(came_from[current_node])
                    current_node = came_from[current_node]
                return path[::-1]

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
            new_position = x, y - 1
        elif action == Action.MOVE_DOWN:
            new_position = x, y + 1
        elif action == Action.MOVE_LEFT:
            new_position = x - 1, y
        elif action == Action.MOVE_RIGHT:
            new_position = x + 1, y
        else:
            new_position = x, y  # Default to the current position for unknown actions

        # Check if the new position is a valid move
        if self.is_valid_move(new_position):
            return new_position
        else:
            return x, y  # If the new position is outside the grid or invalid, stay in the current position

    def is_valid_move(self, node: Tuple[int, int]) -> bool:
        x, y = node
        return 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]) and self.grid[x, y] != Cell.WALL.value

    def tick(self) -> None:
        garbage_start = self.agent_positions[AgentType.GARBAGE]
        vacuum_start = self.agent_positions[AgentType.VACUUM]
        mop_start = self.agent_positions[AgentType.MOP]

        # garbage_goal = self.find_closest_goal(garbage_start, Cell.DRYTRASH)
        vacuum_goal = self.find_closest_goal(vacuum_start, Cell.DUSTY)
        mop_goal = self.find_closest_goal(mop_start, Cell.SOAKED)
        # New goals for cleaning both WETTRASH and DRYTRASH
        garbage_goal_dry = self.find_closest_goal(garbage_start, Cell.DRYTRASH)
        print("this is goal dry",garbage_goal_dry)
        garbage_goal_wet = self.find_closest_goal(garbage_start, Cell.WETTRASH)

        garbage_actions_dry = self.a_star(garbage_start, garbage_goal_dry)
        garbage_actions_wet = self.a_star(garbage_start, garbage_goal_wet)
        
        vacuum_actions = self.a_star(vacuum_start, vacuum_goal)
        mop_actions = self.a_star(mop_start, mop_goal)

        print(self.garbage_pickup_count)
        # Check if the GARBAGE agent should move to the BIN cell
        if self.garbage_pickup_count >= 5:
            garbage_goal_bin = self.find_closest_goal(garbage_start, Cell.BIN)
            garbage_actions_bin = self.a_star(garbage_start, garbage_goal_bin)
            print(garbage_goal_bin)
            print(garbage_actions_bin)

            # Check if the GARBAGE agent is currently en route to the BIN
            if not self.garbage_to_bin:
                # If not, set the flag and start moving towards the BIN
                self.garbage_to_bin = True
                self.garbage_actions_bin = garbage_actions_bin

            # Check if there are remaining actions to take
            if self.garbage_actions_bin:
                next_action = self.garbage_actions_bin.pop(0)  # Pop the next action from the list

                # Check if the next action encounters trash
                new_position = self.apply_action(garbage_start, next_action)
                if self.is_valid_move(new_position):
                    # Update the agent position
                    self.agent_positions[AgentType.GARBAGE] = new_position
                    
                    # return
                    if new_position==garbage_goal_bin:
                        # If trash encountered, reset the flag and start trash picking again
                        self.garbage_to_bin = False
                        self.garbage_pickup_count = 0

                    return
            elif self.agent_positions[AgentType.GARBAGE]==garbage_goal_bin:
                # If no more actions, the GARBAGE agent has reached the BIN
                self.garbage_to_bin = False
                self.garbage_pickup_count = 0
        else:
            # Prioritize one type of trash until it's no longer available
            if garbage_actions_dry and not garbage_actions_wet:
                self.tick_agent(AgentType.GARBAGE, garbage_actions_dry)
            elif garbage_actions_wet and not garbage_actions_dry:
                self.tick_agent(AgentType.GARBAGE, garbage_actions_wet)
            elif garbage_actions_dry and garbage_actions_wet:
                # Both types of trash are available, choose the one with the shorter path
                if len(garbage_actions_dry) <= len(garbage_actions_wet):
                    self.tick_agent(AgentType.GARBAGE, garbage_actions_dry)
                else:
                    self.tick_agent(AgentType.GARBAGE, garbage_actions_wet)


        self.tick_agent(AgentType.VACUUM, vacuum_actions)
        self.tick_agent(AgentType.MOP, mop_actions)

    def tick_agent(self, agent_type: AgentType, actions: List[Action]) -> None:
        for action in actions:
            current_position = self.agent_positions[agent_type]

            # Update the visual grid based on the actions
            if action == Action.MOVE_UP or action == Action.MOVE_DOWN or \
                action == Action.MOVE_LEFT or action == Action.MOVE_RIGHT:
                # Update agent positions if it's a movement action
                new_position = self.apply_action(current_position, action)
                self.agent_positions[agent_type] = new_position

        # # Set the cell value to EMPTY at the final position
        final_position = self.agent_positions[agent_type]
        if agent_type==AgentType.VACUUM and self.grid[final_position[0], final_position[1]]==Cell.DUSTY.value:
            self.grid[final_position[0], final_position[1]] = Cell.EMPTY.value
            print(f"{agent_type.name} vacuumed cell at {final_position}")
        if agent_type==AgentType.MOP and self.grid[final_position[0], final_position[1]]==Cell.SOAKED.value:
            self.grid[final_position[0], final_position[1]] = Cell.EMPTY.value
            print(f"{agent_type.name} mopped cell at {final_position}")
        if agent_type==AgentType.GARBAGE:
            if self.grid[final_position[0], final_position[1]]==Cell.DRYTRASH.value:
                self.garbage_pickup_count+=1
                self.grid[final_position[0], final_position[1]] = Cell.DUSTY.value
                print(f"{agent_type.name} made drytrash cell to dusty at {final_position}")
            if self.grid[final_position[0], final_position[1]]==Cell.WETTRASH.value:
                self.garbage_pickup_count+=1
                self.grid[final_position[0], final_position[1]]=Cell.SOAKED.value
                print(f"{agent_type.name} made wettrash cell to soaked at {final_position}")

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

