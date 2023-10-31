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

    def __init__(self, grid: np.ndarray, agents: list, speed: float = 1, **kwargs):
        """
        Sets up the simulator.

        :param grid: Start state of environment grid
        :param agents: AI agents that clean up the grid
        :param speed: Time between ticks in seconds
        :param kwargs: Passed to ``textual.App.__init__``
        """
        super().__init__(**kwargs)
        self.paused = True

        self.speed = speed
        self.timer: Timer | None = None

        self.canvas = Canvas(200, 200, color=Color(255, 255, 255))
        self.brush = "obstacle"

        self.grid = grid
        self.agents = agents

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)
        self.canvas.draw_circle(100, 100, 50, Color(0, 0, 0))

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.canvas
        yield Footer()

    def tick(self) -> None:
        """Simulation tick updating the state of the agents and environment."""
        # TODO: Agent simulation and grid updates

    def draw_point(self, x: int, y: int, color: Color) -> None:
        """Draws a 2x2 point to the canvas."""
        x *= 2
        y *= 2
        self.canvas.set_pixel(x, y, color)
        self.canvas.set_pixel(x, y + 1, color)
        self.canvas.set_pixel(x + 1, y, color)
        self.canvas.set_pixel(x + 1, y + 1, color)

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
        self.draw_point(x, y, colours[self.brush])
        # TODO: Update grid

    def on_click(self, event: Click) -> None:
        self.update_coords(event.x // 2, event.y)

    def on_mouse_move(self, event: MouseMove) -> None:
        if event.button != 0:
            self.update_coords(event.x // 2, event.y)
