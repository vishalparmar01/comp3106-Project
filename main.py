from argparse import ArgumentParser

from sim import app
from agent.separate_agents import SeparateAgents
from agent.central_manager import CentralManager
from agent.astar_controller import AStarController
from agent.agent_manager import AgentType


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="Trash simulator",
        description="Simulates agents cleaning trash"
    )
    parser.add_argument(
        '-c',
        '--central',
        help="Whether to use the central manager",
        action='store_true',
        default=False
    )
    args = parser.parse_args()

    # simulator = app.Simulator(6, 6, CentralManager if args.central else SeparateAgents, 10)
    simulator = app.Simulator(6, 6, CentralManager, 10)
    astar_controller = AStarController(simulator)
    simulator.run()

    print(simulator.grid)
    print(simulator.agents)



'''
1) How are we showing real time agent movement ----> Do this using a tick function

2) Agent start point // Display ----> 3 places for each agent to start.

3) Trash Bin ???

4) Best path track -> using our algorithm

'''

# access grid square ->
