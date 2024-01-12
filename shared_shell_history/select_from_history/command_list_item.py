from textual.containers import Horizontal
from textual.widgets import Label, ListItem


class CommandListItem(ListItem):
    """
    Custom list item widget for displaying a command.

    Displays command information in a horizontal layout, with each part of the
    command (user name, host, command text) styled separately via CSS.
    """
    def __init__(self, command):
        super().__init__()
        self.command = command

    def compose(self):
        with Horizontal():
            yield Label(self.command.user_name, id="user_name")
            yield Label(self.command.host, id="host")
            yield Label(self.command.command, id="command")
