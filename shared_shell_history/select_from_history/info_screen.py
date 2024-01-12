from textual import on
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class InfoScreen(ModalScreen):
    def __init__(self, command):
        super().__init__()
        self.command = command

    def compose(self):
        with Container():
            yield Label(f"Id: {self.command.id}")
            yield Label(f"User: {self.command.user_name}")
            yield Label(f"Host: {self.command.host}")
            yield Label(f"Path: {self.command.path}")
            yield Label(f"Venv: {self.command.venv}")
            yield Label(f"Time: {self.command.time}")
            yield Label(f"Command: {self.command.command}")
            with Container():
                yield Button.success("Close", id="close")
                yield Label("", id="spacer")
                yield Button.error("Delete", id="delete")

    @on(Button.Pressed)
    def leave_screen(self, event):
        self.dismiss(event.button.id == "delete")
