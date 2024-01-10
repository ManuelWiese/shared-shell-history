from textual.app import App, ComposeResult, Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Label, ListItem, ListView

from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import Session

from model import ShellCommand


class CommandListItem(ListItem):
    def __init__(self, user, host, command):
        super().__init__()
        self.user = user
        self.host = host
        self.command = command

    def compose(self):
        text_width = 10
        with Horizontal():
            yield Label(f"{self.user[:text_width]:<{text_width}} ")
            yield Label(f"{self.host[:text_width]:<{text_width}} ")
            yield Label(self.command)


class CommandHistory(App):
    # CSS_PATH = "list_view.tcss"
    BINDINGS = [
        Binding("q", "quit()", "Quit", priority=True, show=True),
        Binding("u", "select_user()", "Select User", show=True),
        Binding("d", "delete_entry()", "Delete Entry", show=True),
    ]

    def __init__(self, database, tmp_file, user=None, host=None):
        super().__init__()
        self.database = database
        self.tmp_file = tmp_file

        self.username = None
        self.host = None

        self.commands = self.fetch_commands()

    def fetch_commands(self):
        engine = create_engine(self.database)
        with Session(engine) as session:
            query = select(
                ShellCommand.user_name,
                ShellCommand.host,
                ShellCommand.time,
                ShellCommand.command
            ).order_by(
                desc(ShellCommand.id)
            )

            if self.username is not None or self.host is not None:
                conditions = []
                if self.username is not None:
                    conditions.append(ShellCommand.user_name == self.username)
                if self.host is not None:
                    conditions.append(ShellCommand.host == self.host)
                query = query.where(*conditions)

            commands = session.execute(query).mappings().all()

        return commands

    def compose(self) -> ComposeResult:
        list_items = (
            CommandListItem(
                command["user_name"],
                command["host"],
                command["command"]
            )
            for command in self.commands
        )

        yield ListView(
            *list_items
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        command = event.item.command
        with open(self.tmp_file, "w") as f:
            f.write(command)
        exit()

    def action_quit(self):
        exit()

    def action_select_user(self):
        self.mount(Label("HALLO"))

    def action_delete_entry(self):
        self.mount(Label("Delete"))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=str, required=True)
    parser.add_argument("--tmp_file", type=str, required=True)
    parser.add_argument("--user", type=str, default=None)
    arguments = parser.parse_args()

    app = CommandHistory(
        database=arguments.database,
        user=arguments.user,
        tmp_file=arguments.tmp_file
    )
    app.run()
