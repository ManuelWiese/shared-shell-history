from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, SelectionList


class SelectionScreen(ModalScreen):
    BINDINGS = [
        Binding("a", "select_all()", "Select All"),
        Binding("o", "select_one()", "Select One"),
    ]

    def __init__(self, title, values, currently_selected):
        super().__init__()
        self.title = title
        self.values = values
        self.currently_selected = currently_selected

    def compose(self):
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
            yield Button("OK", id="ok")

    def on_mount(self):
        self.query_one(SelectionList).border_title = self.title

    @on(Button.Pressed)
    def button_pressed(self, event):
        if event.button.id == "all":
            self.action_select_all()
        elif event.button.id == "one":
            self.action_select_one()
        elif event.button.id == "ok":
            selected = self.query_one(SelectionList).selected
            self.dismiss(selected)

    def action_select_all(self):
        self.query_one(SelectionList).select_all()

    def action_select_one(self):
        self.query_one(SelectionList).deselect_all()
        self.query_one(SelectionList)._toggle_highlighted_selection()
