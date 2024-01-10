from textual import on
from textual.app import App, ComposeResult, Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Label, ListItem, ListView
from textual.screen import ModalScreen

from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import Session

from model import ShellCommand


class CommandListItem(ListItem):
    def __init__(self, command):
        super().__init__()
        self.command = command

    def compose(self):
        text_width = 10
        with Horizontal():
            yield Label(f"{self.command.user_name[:text_width]:<{text_width}} ")
            yield Label(f"{self.command.host[:text_width]:<{text_width}} ")
            yield Label(self.command.command)


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
            with Horizontal():
                yield Button("Close", id="close")
                yield Button.error("Delete", id="delete")

    @on(Button.Pressed)
    def leave_modal_screen(self, event):
        self.dismiss()


class CommandHistory(App):
    CSS_PATH = "select_from_history.tcss"
    BINDINGS = [
        Binding("q", "quit()", "Quit", priority=True, show=True),
        Binding("u", "select_user()", "Select User", show=True),
        Binding("h", "select_host()", "Select Host", show=True),
        Binding("i", "show_info()", "Show Info", show=True),
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
                ShellCommand
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

            commands = session.execute(query).all()

        return [command for (command, ) in commands]

    def compose(self) -> ComposeResult:
        list_items = self.get_list_items()

        yield ListView(*list_items, id="command_list_view")
        yield Footer()

    def get_list_items(self):
        return (
            CommandListItem(command)
            for command in self.commands
        )

    def on_list_view_selected(self, event: ListView.Selected):
        command = event.item.command.command
        with open(self.tmp_file, "w") as f:
            f.write(command)
        exit()

    def action_quit(self):
        exit()

    def action_select_user(self):
        self.mount(Label("HALLO"))

    def action_show_info(self):
        command_list_view = self.get_child_by_id(id="command_list_view")
        command = self.commands[command_list_view.index]
        self.push_screen(InfoScreen(command))

    def action_delete_entry(self):
        self.delete_entry()

    def delete_entry(self):
        command_list_view = self.get_child_by_id(id="command_list_view")
        index = command_list_view.index
        command = self.commands[index]

        # TODO: delete from database

        del self.commands[index]
        command_list_view.clear()
        command_list_view.extend(self.get_list_items())
        # select the item above the deleted item
        command_list_view.index = max(index - 1, 0)


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
