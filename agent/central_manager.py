import numpy as np

from agent.agent_manager import AgentManager, AgentType


class CentralManager(AgentManager):
    def __init__(self, grid: np.ndarray):
        super().__init__(grid)

    def tick(self) -> None:
        pass

    def agent_locations(self) -> dict[AgentType: tuple[int, int]]:
        return {}

    def __repr__(self) -> str:
        return ""
