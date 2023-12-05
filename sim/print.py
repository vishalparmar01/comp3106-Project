from typing import Any, Callable


class Printer:
    def __init__(self):
        self.print: Callable[[*Any], None] = print


printer = Printer()

def print(*args: Any):
    printer.print(*args)
