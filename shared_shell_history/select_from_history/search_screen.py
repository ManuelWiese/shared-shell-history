from textual import on
from textual.screen import ModalScreen
from textual.widgets import Input


class SearchScreen(ModalScreen):
    """
    A screen for inputting a search query, specifically for searching commands.

    This screen displays an input field where users can enter a regex or search string 
    to filter commands.

    Attributes:
        current_regex (str): The current regular expression or search string used for filtering.
    """
    def __init__(self, current_regex):
        """
        Initializes the SearchScreen with the current search string.

        Args:
            current_regex (str): The current regular expression or search string.
        """
        super().__init__()
        self.current_regex = current_regex

    def compose(self):
        """
        Composes the screen with an Input widget for entering the search query.
        """
        yield Input(placeholder="Search command...")

    def on_mount(self):
        """
        Called when the screen is mounted. Sets the initial value of the input
        field to the current regex.
        """
        self.query_one(Input).value = self.current_regex

    @on(Input.Submitted)
    def close(self, event):
        """
        Handles the event when the search query is submitted.

        Closes the screen and returns the entered search query.

        Args:
            event: The event object containing the submitted input.
        """
        self.dismiss(
            self.query_one(Input).value
        )
