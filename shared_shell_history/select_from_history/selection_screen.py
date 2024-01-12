from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, SelectionList


class SelectionScreen(ModalScreen):
    """
    A custom screen for selecting items from a list.

    This screen displays a list of items and allows the user to select one or more items.
    It supports selecting all items, deselecting all, or manually selecting individual items.

    Attributes:
        title (str): The title of the selection screen.
        values (list): A list of values to be displayed for selection.
        currently_selected (list): A list of values that are currently selected.
    """
    BINDINGS = [
        Binding("a", "select_all()", "Select All"),
        Binding("o", "select_one()", "Select One"),
        Binding("c", "confirm()", "Confirm Current Selection"),
    ]

    def __init__(self, title, values, currently_selected):
        """
        Initializes the SelectionScreen with a title, values for selection,
        and currently selected items.

        Args:
            title (str): The title of the screen.
            values (list): The values to be displayed for selection.
            currently_selected (list): The values that are currently selected.
        """
        super().__init__()
        self.title = title
        self.values = values
        self.currently_selected = currently_selected

    def compose(self):
        """
        Composes the SelectionList and Buttons for the screen.
        """
        sorted_values = sorted(self.values)
        selection_list_items = (
            (value, value, value in self.currently_selected)
            for value in sorted_values
        )
        yield SelectionList[str](
            *selection_list_items
        )
        with Horizontal():
            yield Button("Select (a)ll", id="all")
            yield Button("Select (o)ne", id="one")
            yield Button("(C)onfirm", id="confirm")

    def on_mount(self):
        """
        Called when the screen is mounted. Sets the border title of the selection list.
        """
        self.query_one(SelectionList).border_title = self.title

    @on(Button.Pressed)
    def button_pressed(self, event):
        """
        Handles button press events.

        Args:
            event: The event object containing the button pressed.
        """
        if event.button.id == "all":
            self.action_select_all()
        elif event.button.id == "one":
            self.action_select_one()
        elif event.button.id == "confirm":
            self.confirm()

    def confirm(self):
        """
        Finalize the selection and close the screen.

        This method retrieves the currently selected items from the SelectionList widget and 
        then uses the 'dismiss' method to close the SelectionScreen, returning the selected items.
        """
        selected = self.query_one(SelectionList).selected
        self.dismiss(selected)

    def action_select_all(self):
        """
        Selects all items in the selection list.
        """
        self.query_one(SelectionList).select_all()

    def action_select_one(self):
        """
        Deselects all items and then selects the currently highlighted item in the selection list.
        """
        self.query_one(SelectionList).deselect_all()
        self.query_one(SelectionList)._toggle_highlighted_selection()

    def action_confirm(self):
        """
        Trigger the confirmation action.

        This method is typically bound to a key in the UI and invokes the 'confirm' method 
        to finalize the selection and close the screen.
        """
        self.confirm()
