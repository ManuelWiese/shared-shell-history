from textual import on
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class InfoScreen(ModalScreen):
    """
    A screen that displays detailed information about a selected command.

    This screen shows various attributes of a command, such as user, host, execution path, etc.,
    and provides options to close the screen or delete the command.

    Attributes:
        command (ShellCommand): The command object containing information to display.
    """
    def __init__(self, command):
        """
        Initializes the InfoScreen with the specified command.

        Args:
            command (ShellCommand): The command object whose details are to be displayed.
        """
        super().__init__()
        self.command = command

    def compose(self):
        """
        Composes the screen with labels to display the command's information
        and buttons for actions.
        """
        with Container():
            yield Label(f"Id: {self.command.id}")
            yield Label(f"User: {self.command.user_name}")
            yield Label(f"Host: {self.command.host}")
            yield Label(f"Path: {self.command.path}")
            yield Label(f"Venv: {self.command.venv}")
            yield Label(f"Time: {self.command.time}")
            yield Label(f"Command: {self.command.command}")
            with Container():
                yield Button("Close", id="close")
                yield Button.error("Delete", id="delete")

    @on(Button.Pressed)
    def leave_screen(self, event):
        """
        Handles button press events.

        Closes the screen when 'Close' is pressed, or closes and triggers the deletion
        process if 'Delete' is pressed.

        Args:
            event: The event object containing information about the pressed button.
        """
        self.dismiss(event.button.id == "delete")
