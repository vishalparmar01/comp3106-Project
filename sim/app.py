from typing import Type

from textual.app import App, ComposeResult
from textual.color import Color
from textual.events import MouseMove, Click
from textual.timer import Timer
from textual.widgets import Footer, Header
from textual_canvas import Canvas

from agent.agent_manager import AgentManager, AgentType
from grid.grid import create_dynamic_grid, Cell, get_start_positions


colours = {
    Cell.EMPTY: Color(255, 255, 255),
    Cell.DRY: Color(255, 0, 0),
    Cell.WET: Color(0, 0, 255),
    Cell.DIRTY: Color(127, 0, 0),
    Cell.BIN: Color(0, 255, 0),
    Cell.WALL: Color(0, 0, 0),
    AgentType.GARBAGE: Color(255, 255, 0),
    AgentType.VACUUM: Color(0, 255, 255),
    AgentType.MOP: Color(255, 0, 255),
}


class Simulator(App[None]):
    """Simulates an environment and runs the agents."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Toggle pause/resume"),
        ("e", "select_erase", "Place empty"),
        ("b", "select_bin", "Place bin"),
        ("o", "select_obstacle", "Place obstacle"),
        ("t", "select_trash", "Place trash"),
        ("w", "select_wet", "Place wet"),
    ]

    def __init__(
        self,
        rows: int,
        cols: int,
        Manager: Type[AgentManager],
        scale_factor: int = 2,
        speed: float = 1,
        **kwargs
    ):
        """
        Sets up the simulator.

        :param grid: Start state of environment grid
        :param Manager: AI agents that clean up the grid
        :param speed: Time between ticks in seconds
        :param kwargs: Passed to ``textual.App.__init__``
        """
        super().__init__(**kwargs)

        self.rows = rows
        self.cols = cols
        self.grid = create_dynamic_grid(rows, cols)

        self.paused = True

        self.speed = speed
        self.timer: Timer | None = None

        self.canvas = Canvas(cols * scale_factor, rows * scale_factor, color=Color(255, 255, 255))
        self.brush = Cell.EMPTY

        self.scale_factor = scale_factor
        self.agents = Manager(self.grid, get_start_positions(self.grid))

    def set_grid_size(self, rows: int, cols: int):
        """Set the size of the grid dynamically."""
        self.rows = rows
        self.cols = cols
        self.grid = create_dynamic_grid(rows, cols)
        self.canvas = Canvas(cols * 2, rows * 2, color=Color(255, 255, 255))

    def draw_grid(self) -> None:
        for i in range(self.rows):
            for j in range(self.cols):
                self.draw_point(i, j, colours[Cell(self.grid[i, j])])

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)
        self.draw_grid()
        self.draw_agents()

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.canvas
        yield Footer()

    def draw_agents(self):
        agents = self.agents.agent_locations()
        for agent in agents:
            x, y = agents[agent]
            x *= self.scale_factor
            y *= self.scale_factor
            for i in range(1, self.scale_factor - 1):
                for j in range(1, self.scale_factor - 1):
                    self.canvas.set_pixel(x + i, y + j, colours[agent])

    def tick(self) -> None:
        """Simulation tick updating the state of the agents and environment."""
        self.agents.tick()
        self.draw_grid()
        self.draw_agents()

    def draw_point(self, x: int, y: int, color: Color) -> None:
        """Draws a scaled point to the canvas."""
        x *= self.scale_factor
        y *= self.scale_factor
        for i in range(self.scale_factor):
            for j in range(self.scale_factor):
                self.canvas.set_pixel(x + i, y + j, color)

    def action_toggle_pause(self) -> None:
        """Toggles the timer."""
        if self.paused:
            self.timer.resume()
        else:
            self.timer.pause()

        self.paused = not self.paused

    def action_select_erase(self) -> None:
        self.brush = Cell.EMPTY

    def action_select_bin(self) -> None:
        self.brush = Cell.BIN

    def action_select_obstacle(self) -> None:
        self.brush = Cell.WALL

    def action_select_trash(self) -> None:
        self.brush = Cell.DRY

    def action_select_wet(self) -> None:
        self.brush = Cell.WET

    def handle_click(self, raw_x: int, raw_y: int):
        # Calculate the grid coordinates based on the clicked pixel
        x = raw_x // self.scale_factor
        y = raw_y // (self.scale_factor // 2)

        if x >= self.cols or y >= self.rows:
            return

        # Change the color of the clicked grid square to green
        self.draw_point(x, y, colours[self.brush])  # You can use any color you want

        # Update the grid to indicate the presence of an element (e.g., bin)
        self.grid[x, y] = self.brush.value  # Adjust as needed based on your grid representation

    def on_click(self, event: Click) -> None:
        self.handle_click(event.x, event.y)

    def on_mouse_move(self, event: MouseMove) -> None:
        if event.button != 0:
            self.handle_click(event.x, event.y)
