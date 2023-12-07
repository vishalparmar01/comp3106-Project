from random import seed, random
from time import perf_counter
from typing import Type

from rich.text import Text
from rich.traceback import Traceback
from textual.app import App, ComposeResult
from textual.color import Color
from textual.containers import Container, Horizontal, Vertical
from textual.events import Click, MouseDown, MouseMove, MouseScrollDown, MouseScrollUp, MouseUp
from textual.timer import Timer
from textual.widgets import Footer, Header, RichLog, Label
from textual_canvas import Canvas

from agent.agent_manager import AgentManager, AgentType, AGENT_TARGETS, get_start_positions
from grid.grid import create_dynamic_grid, Cell
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
    yield Label("Agents:")
    for agent in AgentType:
        text = Text(f"██ {agent.name.title()}")
        text.stylize(colours[agent].css, 0, 2)
        yield Label(text)


def cell_legend():
    yield Label("Cells: ")
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
        ("p", "toggle_pause", "Pause"),
        ("l", "toggle_logs", "Show log"),
        ("e", "select_erase", "Erase"),
        ("b", "select_bin", "Bin"),
        # ("o", "select_obstacle", "Obstacle"),
        ("t", "select_trash", "Dry"),
        ("w", "select_wet", "Wet"),
        ("d", "select_dusty", "Dusty"),
        ("s", "select_soaked", "Soaked"),
        ("+", "zoom_in", "Zoom in"),
        ("-", "zoom_out", "Zoom out"),
        ("r", "reset", "Reset"),
        ("R", "reset_seed", "Restart"),
        ("g", "focus_garbage", "Garbage view"),
        ("m", "focus_mop", "Mop view"),
        ("v", "focus_vacuum", "Vacuum view"),
        ("ctrl+up", "speed_up", "Speed up"),
        ("ctrl+down", "slow_down", "Slow down")
    ]

    CSS_PATH = "styles.tcss"

    def __init__(
        self,
        rows: int,
        cols: int,
        Manager: Type[AgentManager],
        scale_factor: int,
        speed: float,
        rng_seed: float | None,
        grid_fill: float,
        grid_garbage_proportion: float,
        grid_bins: int,
        tests: int,
        random_start: bool,
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
        printer.print = lambda *args: self.logger.write(args)\
            if len(args) > 1\
            else self.logger.write(args[0] if args else "")

        self.rows = rows
        self.cols = cols
        self.regenerate_grid = lambda: create_dynamic_grid(cols, rows, grid_fill, grid_garbage_proportion, grid_bins)
        self.grid = self.regenerate_grid()

        self.num_tests = tests
        self.results: dict[float, int] = {}
        self.paused = not bool(self.num_tests)

        self.speed = speed
        self.timer: Timer | None = None

        self.canvas = Canvas(cols * scale_factor, rows * scale_factor, color=BACKGROUND_COLOUR)
        self.brush = Cell.EMPTY

        self.scale_factor = scale_factor
        self.original_scale_factor = scale_factor

        self.Manager = Manager
        self.randomise_start_positions = random_start
        self.agents = Manager(self.grid, get_start_positions(self.grid, self.randomise_start_positions))

        self.ticks = 0
        self.calculation_time = 0.

        self.resizing = False
        self.view: AgentType | None = None

        self.motd()

    def motd(self) -> None:
        if self.num_tests:
            print(f"Test {len(self.results) + 1}/{self.num_tests}")
        print(f"RNG Seed: {self.seed}")

    def draw_grid(self) -> None:
        for i in range(self.rows):
            for j in range(self.cols):
                cell = Cell(self.grid[j, i])
                if self.view and Cell(self.grid[j, i]) not in AGENT_TARGETS[self.view]:
                    cell = Cell.EMPTY
                self.draw_point(j, i, colours[cell])

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

    @property
    def probably_looping(self) -> bool:
        return self.ticks > (max(self.rows, self.cols) ** 2) * 10

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
        return (agents_finished and grid_finished) or self.probably_looping

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
            if self.num_tests:
                self.results[self.seed] = self.ticks
            if len(self.results) < self.num_tests:
                return self.reset(True)
            self.timer.pause()
            self.paused = True
            if self.probably_looping:
                print("ERROR - Quitting as the number of ticks is excessively high")

            if self.num_tests and len(self.results) == self.num_tests:
                self.logger.clear()
                print(self.results)
                print()
                print(f"Completed running {self.num_tests} tests")
                print(f"Average ticks: {sum(self.results.values()) / self.num_tests:0.2f}")
            else:
                print(f"Completed in {self.ticks} ticks")
                print(f"Calculation time of {self.calculation_time} seconds")
                print(f"{self.calculation_time/self.ticks} seconds/tick")

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

    def on_mouse_up(self, _event: MouseUp):
        self.resizing = False

    def reset(self, change_seed: bool):
        self.logger.clear()
        if change_seed:
            self.seed = random()
        seed(self.seed)
        self.motd()
        if not self.paused and len(self.results) >= self.num_tests:
            self.paused = True
            self.timer.pause()
        self.grid = self.regenerate_grid()
        self.agents = self.Manager(self.grid, get_start_positions(self.grid, self.randomise_start_positions))
        self.ticks = 0
        self.calculation_time = 0
        self.draw_ui()

    def action_reset(self):
        self.reset(False)

    def action_reset_seed(self):
        self.reset(True)

    def action_focus_garbage(self):
        self.view = None if self.view == AgentType.GARBAGE else AgentType.GARBAGE
        self.draw_ui()

    def action_focus_mop(self):
        self.view = None if self.view == AgentType.MOP else AgentType.MOP
        self.draw_ui()

    def action_focus_vacuum(self):
        self.view = None if self.view == AgentType.VACUUM else AgentType.VACUUM
        self.draw_ui()

    def action_speed_up(self):
        self.speed = max(0.01, self.speed / 2)
        self.timer.stop()
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)

    def action_slow_down(self):
        self.speed = min(5., self.speed * 2)
        self.timer.stop()
        self.timer = self.set_interval(self.speed, self.tick, pause=self.paused)
