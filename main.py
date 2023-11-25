import numpy as np

from sim import app


if __name__ == "__main__":
    simulator = app.Simulator(6, 6, np.array([]), 10)
    simulator.run()
    print(simulator.grid)


'''
1) How are we showing real time agent movement ----> Do this using a tick function

2) Agent start point // Display ----> 3 places for each agent to start.

3) Trash Bin ???

4) Best path track -> using our algorithm

'''

# access grid square ->
