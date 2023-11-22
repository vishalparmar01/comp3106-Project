from random import choice, randint

import numpy as np
from textual.app import App, ComposeResult
from textual.color import Color
from textual.events import MouseMove, Click
from textual.timer import Timer
from textual.widgets import Footer, Header
from textual_canvas import Canvas


colours = {
    "erase": Color(255, 255, 255),
    "bin": Color(0, 255, 0),
    "obstacle": Color(0, 0, 0),
    "trash": Color(255, 0, 0),
    "wet": Color(0, 0, 255),
    "empty": Color(255,255,255)
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

    def __init__(self, rows: int, cols: int, agents: list, scale_factor: int = 2, speed: float = 1, **kwargs):
        """
        Sets up the simulator.

        :param grid: Start state of environment grid
        :param agents: AI agents that clean up the grid
        :param speed: Time between ticks in seconds
        :param kwargs: Passed to ``textual.App.__init__``
        """
        super().__init__(**kwargs)

        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols), dtype=np.uint8)  # Initialize grid with zeros

        self.paused = True

        self.speed = speed
        self.timer: Timer | None = None

        self.canvas = Canvas(cols * scale_factor, rows * scale_factor, color=Color(255, 255, 255))
        self.brush = "obstacle"

        self.grid = np.zeros((rows, cols), dtype=np.uint8)

        print(self.grid)
        self.scale_factor = scale_factor
        self.agents = agents

    def set_grid_size(self, rows: int, cols: int):
        """Set the size of the grid dynamically."""
        self.rows = rows
        self.cols = cols
        self.grid = np.zeros((rows, cols), dtype=np.uint8)
        self.canvas = Canvas(cols * 2, rows * 2, color=Color(255, 255, 255))


    def on_mount(self) -> None:
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)
        # TODO: Draw initial state
        # self.canvas.draw_circle(100, 100, 50, Color(0, 0, 0))
        # super().on_mount()
        # Populate the grid with randomly allocated wet or trash
        # Populate the grid with wet or trash in 50% of the cells
        for i in range(self.rows):
            for j in range(self.cols):
                if randint(0, 1):  # Randomly choose whether to place wet or trash
                    element = choice(["wet", "trash"])
                    self.grid[i, j] = 1  # Indicate the presence of an element in the grid
                else:
                    element = "empty"
                self.draw_point(i, j, colours[element])


    def compose(self) -> ComposeResult:
        yield Header()
        yield self.canvas
        yield Footer()

    def tick(self) -> None:
        """Simulation tick updating the state of the agents and environment."""
        # TODO: Agent simulation and grid updates
        self.draw_point(0, 0, Color(randint(0, 255), randint(0, 255), randint(0, 255)))

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
        self.brush = "erase"

    def action_select_bin(self) -> None:
        self.brush = "bin"

    def action_select_obstacle(self) -> None:
        self.brush = "obstacle"

    def action_select_trash(self) -> None:
        self.brush = "trash"

    def action_select_wet(self) -> None:
        self.brush = "wet"

    def update_coords(self, x: int, y: int):
        # Update grid based on the coordinates
        self.grid[x, y] = 1  # For simplicity, setting to 1 to indicate an obstacle
        self.draw_point(x, y, colours[self.brush])

    def on_click(self, event: Click) -> None:
        # Calculate the grid coordinates based on the clicked pixel
        x = event.x // self.scale_factor
        y = (event.y // self.scale_factor) * 2

        # Change the color of the clicked grid square to green
        self.draw_point(x, y, colours["bin"])  # You can use any color you want

        # Update the grid to indicate the presence of an element (e.g., bin)
        self.grid[x, y] = 1  # Adjust as needed based on your grid representation

    def on_mouse_move(self, event: MouseMove) -> None:
        if event.button != 0:
            self.update_coords(event.x // 2, event.y)
