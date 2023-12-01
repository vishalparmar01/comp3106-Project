#!/bin/env python
from argparse import ArgumentParser

from sim import app
from agent.separate_agents import SeparateAgents
from agent.astar_controller import AStarController


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Trash simulator",
        description="Simulates agents cleaning trash"
    )
    parser.add_argument(
        '-i',
        '--individual',
        help="Whether to use the individually managed agents",
        action='store_true',
        default=False
    )
    parser.add_argument(
        '-x',
        '--columns',
        help="How many columns in the grid",
        type=int,
        default=10
    )
    parser.add_argument(
        '-y',
        '--rows',
        help="How many rows in the grid",
        type=int,
        default=6
    )
    parser.add_argument(
        '-s',
        '--scale',
        help="Scale of the grid display",
        type=int,
        default=6
    )
    parser.add_argument(
        '-d',
        '--delta',
        help="Time between simulation ticks in seconds",
        type=float,
        default=0.5
    )
    args = parser.parse_args()

    simulator = app.Simulator(
        args.rows,
        args.columns,
        SeparateAgents if args.individual else AStarController,
        args.scale,
        args.delta
    )
    simulator.run()

    print(simulator.grid.T)
    print(simulator.agents)



'''
1) How are we showing real time agent movement ----> Do this using a tick function

2) Agent start point // Display ----> 3 places for each agent to start.

3) Trash Bin ???

4) Best path track -> using our algorithm

'''

# access grid square ->
