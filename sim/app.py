from random import seed, random
from time import perf_counter
from typing import Type

from rich.text import Text
from rich.traceback import Traceback
from textual.app import App, ComposeResult
from textual.color import Color
from textual.containers import Container, Horizontal, HorizontalScroll, Vertical
from textual.events import Click, MouseDown, MouseMove, MouseScrollDown, MouseScrollUp, MouseUp
from textual.timer import Timer
from textual.widgets import Footer, Header, RichLog, Label
from textual_canvas import Canvas

from agent.agent_manager import AgentManager, AgentType
from grid.grid import create_dynamic_grid, Cell, get_start_positions
from sim.print import printer, print


colours = {
    Cell.EMPTY: Color(255, 255, 255),
    Cell.DRYTRASH: Color(255, 0, 0),
    Cell.WETTRASH: Color(0, 0, 255),
    Cell.DUSTY: Color(63, 0, 0),
    Cell.SOAKED: Color(0, 0, 63),
    Cell.BIN: Color(0, 255, 0),
    Cell.WALL: Color(0, 0, 0),
    AgentType.GARBAGE: Color(255, 255, 0),
    AgentType.VACUUM: Color(255, 0, 255),
    AgentType.MOP: Color(0, 255, 255),
}

BACKGROUND_COLOUR = colours[Cell.EMPTY]


def agent_legend():
    for agent in AgentType:
        text = Text(f"██ {agent.name.title()}")
        text.stylize(colours[agent].css, 0, 2)
        yield Label(text)


def cell_legend():
    for cell in Cell:
        if cell in (Cell.WALL, Cell.EMPTY):
            continue
        text = Text(f"██ {cell.name.title()}")
        text.stylize(colours[cell].css, 0, 2)
        yield Label(text)


class Simulator(App[None]):
    """Simulates an environment and runs the agents."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "toggle_pause", "Toggle pause/resume"),
        ("l", "toggle_logs", "Toggle logs"),
        ("e", "select_erase", "Place empty"),
        ("b", "select_bin", "Place bin"),
        ("o", "select_obstacle", "Place obstacle"),
        ("d", "select_trash", "Place dry trash"),
        ("w", "select_wet", "Place wet trash"),
        ("d", "select_dusty", "Place dusty square"),
        ("s", "select_soaked", "Place soaked square"),
        ("+", "zoom_in", "Zoom in"),
        ("-", "zoom_out", "Zoom out"),
        ("r", "reset", "Reset"),
        ("R", "reset_seed", "Reset w/ new seed"),
    ]

    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        rows: int,
        cols: int,
        Manager: Type[AgentManager],
        scale_factor: int = 2,
        speed: float = 1,
        rng_seed: float | None = None,
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

        self.seed = rng_seed if rng_seed is not None else random()
        seed(self.seed)

        self.logger = RichLog()
        # self.logger.display = False
        printer.print = lambda *args: self.logger.write(args) if len(args) > 1 else self.logger.write(args[0])
        self.log_motd()

        self.rows = rows
        self.cols = cols
        self.grid = create_dynamic_grid(cols, rows)

        self.paused = True

        self.speed = speed
        self.timer: Timer | None = None

        self.canvas = Canvas(cols * scale_factor, rows * scale_factor, color=BACKGROUND_COLOUR)
        self.brush = Cell.EMPTY

        self.scale_factor = scale_factor
        self.original_scale_factor = scale_factor

        self.Manager = Manager
        self.agents = Manager(self.grid, get_start_positions(self.grid))

        self.ticks = 0
        self.calculation_time = 0.

        self.resizing = False

    def log_motd(self):
        print(f"RNG seed: {self.seed}")
        print("Yellow Agent: Garbage Collector -> Pick Dry and Wet Trash.")
        print("Cyan Agent: Vacuum Cleaner -> Clean dusty squares.")
        print("Pink Agent: Mop -> Clean soaked squares.")

    def draw_grid(self) -> None:
        for i in range(self.rows):
            for j in range(self.cols):
                self.draw_point(j, i, colours[Cell(self.grid[j, i])])

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)
        self.draw_ui()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield self.canvas
            with Vertical():
                with Horizontal():
                    for label in agent_legend():
                        yield label
                with Horizontal():
                    for label in cell_legend():
                        yield label
            yield self.logger
        yield Footer()

    def draw_agents(self) -> None:
        agents = self.agents.agent_locations()
        for agent in agents:
            x, y = agents[agent]
            x *= self.scale_factor
            y *= self.scale_factor
            draw_range = (1, self.scale_factor - 1) if self.scale_factor > 2 else (0, self.scale_factor)
            for i in range(*draw_range):
                for j in range(*draw_range):
                    self.canvas.set_pixel(x + i, y + j, colours[agent])

    def draw_ui(self) -> None:
        self.draw_grid()
        self.draw_agents()

    def finished_sim(self) -> bool:
        grid_finished = not any(
            cell.value in self.grid for cell in [
                Cell.SOAKED,
                Cell.WETTRASH,
                Cell.DUSTY,
                Cell.DRYTRASH
            ]
        )
        agents_finished = self.agents.finished()
        if agents_finished and not grid_finished:
            self.log("Error: Agents incorrectly think grid is clean")
        return agents_finished and grid_finished

    def tick(self) -> None:
        """Simulation tick updating the state of the agents and environment."""
        self.ticks += 1
        assert self.timer
        try:
            pre_tick = perf_counter()
            self.agents.tick()
            post_tick = perf_counter()
            self.calculation_time += post_tick - pre_tick
            agents = self.agents.agent_locations()
            if len(set(agent for agent in agents.values())) != len(agents):
                print("ERROR: AGENTS OVERLAPPING")
            self.draw_grid()
            self.draw_agents()
        except Exception:
            self.timer.pause()
            self.paused = True
            print(Traceback(show_locals=True))
        if self.finished_sim():
            self.timer.pause()
            self.paused = True
            print(f"Completed in {self.ticks} ticks")
            print(f"Calculation time of {self.calculation_time} seconds")
            print(f"{self.calculation_time/self.ticks} seconds/tick")
            self.ticks = 0
            self.calculation_time = 0.

    def draw_point(self, x: int, y: int, color: Color) -> None:
        """Draws a scaled point to the canvas."""
        x *= self.scale_factor
        y *= self.scale_factor
        for i in range(self.scale_factor):
            for j in range(self.scale_factor):
                self.canvas.set_pixel(x + i, y + j, color)

    def action_toggle_pause(self) -> None:
        """Toggles the timer."""
        assert self.timer
        if self.paused:
            self.timer.resume()
        else:
            self.timer.pause()

        self.paused = not self.paused

    def action_toggle_logs(self) -> None:
        self.logger.display = not self.logger.display

    def action_select_erase(self) -> None:
        self.brush = Cell.EMPTY

    def action_select_bin(self) -> None:
        self.brush = Cell.BIN

    def action_select_obstacle(self) -> None:
        self.brush = Cell.WALL

    def action_select_trash(self) -> None:
        self.brush = Cell.DRYTRASH

    def action_select_wet(self) -> None:
        self.brush = Cell.WETTRASH

    def action_select_dusty(self) -> None:
        self.brush = Cell.DUSTY

    def action_select_soaked(self) -> None:
        self.brush = Cell.SOAKED

    def action_zoom_in(self) -> None:
        self.scale_factor = min(self.scale_factor + 1, self.original_scale_factor)
        self.canvas.clear(BACKGROUND_COLOUR)
        self.draw_ui()

    def action_zoom_out(self) -> None:
        self.scale_factor = min(max(1, self.scale_factor - 1), self.original_scale_factor)
        self.canvas.clear(BACKGROUND_COLOUR)
        self.draw_ui()

    def handle_click(self, raw_x: int, raw_y: int):
        # Calculate the grid coordinates based on the clicked pixel
        x = (raw_x + int(self.canvas.scroll_x)) // self.scale_factor
        y = (raw_y + int(self.canvas.scroll_y)) // (self.scale_factor // 2)

        if x >= self.cols or y >= self.rows:
            return

        # Change the color of the clicked grid square to green
        self.draw_point(x, y, colours[self.brush])  # You can use any color you want
        if (x, y) in self.agents.agent_locations().values():
            self.draw_agents()

        # Update the grid to indicate the presence of an element (e.g., bin)
        self.grid[x, y] = self.brush.value  # Adjust as needed based on your grid representation

    def on_click(self, event: Click) -> None:
        if event.x == event.screen_x:
            self.handle_click(event.x, event.y)

    def on_mouse_move(self, event: MouseMove) -> None:
        if event.button == 0:
            self.resizing = False
        if self.resizing:
            self.logger.styles.width = self.screen.size.width - event.screen_x
        elif event.button != 0 and event.x == event.screen_x:
            self.handle_click(event.x, event.y)

    def on_mouse_scroll_down(self, event: MouseScrollDown):
        if event.meta:
            self.action_zoom_in()

    def on_mouse_scroll_up(self, event: MouseScrollUp):
        if event.meta:
            self.action_zoom_out()

    def on_mouse_down(self, event: MouseDown):
        if 0 == event.x != event.screen_x:
            self.resizing = True

    def on_mouse_up(self, _event: MouseDown):
        self.resizing = False

    def reset(self, change_seed: bool):
        self.logger.clear()
        self.log_motd()
        if change_seed:
            self.seed = random()
        seed(self.seed)
        if not self.paused:
            self.paused = True
            self.timer.pause()
        self.grid = create_dynamic_grid(self.cols, self.rows)
        self.agents = self.Manager(self.grid, get_start_positions(self.grid))
        self.ticks = 0
        self.calculation_time = 0
        self.draw_ui()

    def action_reset(self):
        self.reset(False)

    def action_reset_seed(self):
        self.reset(True)
