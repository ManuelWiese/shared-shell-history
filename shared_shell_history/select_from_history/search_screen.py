from textual import on
from textual.screen import ModalScreen
from textual.widgets import Input


class SearchScreen(ModalScreen):
    def __init__(self, current_regex):
        super().__init__()
        self.current_regex = current_regex

    def compose(self):
        yield Input(placeholder="Search command...")

    def on_mount(self):
        self.query_one(Input).value = self.current_regex

    @on(Input.Submitted)
    def close(self, event):
        self.dismiss(
            self.query_one(Input).value
        )
