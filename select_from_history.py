from textual import on
from textual.app import App, ComposeResult, Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Label, ListItem, ListView, SelectionList
from textual.screen import ModalScreen

from sqlalchemy import create_engine, select, desc, delete, distinct
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
        self.dismiss(event.button.id == "delete")


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

        # TODO: remove this members
        self.username = user
        self.host = host

        self.commands = self.fetch_commands()
        self.usernames = self.fetch_users()
        self.hosts = self.fetch_hosts()

        if user is None:
            self.selected_usernames = self.usernames
        else:
            self.selected_usernames = [user]

        if host is None:
            self.selected_hosts = self.hosts
        else:
            self.selected_hosts = [host]

    def fetch_users(self):
        engine = create_engine(self.database)
        with Session(engine) as session:
            query = select(
                distinct(
                    ShellCommand.user_name
                )
            )

            results = session.execute(query).all()

        return [result[0] for result in results]

    def fetch_hosts(self):
        engine = create_engine(self.database)
        with Session(engine) as session:
            query = select(
                distinct(
                    ShellCommand.host
                )
            )

            results = session.execute(query).all()

        return [result[0] for result in results]

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
        self.push_screen(
            SelectionScreen(
                "Select user(s)",
                self.usernames,
                self.selected_usernames
            ),
            self.set_selected_users
        )

    def set_selected_users(self, selected_usernames):
        self.selected_usernames = selected_usernames

    def action_show_info(self):
        command_list_view = self.get_child_by_id(id="command_list_view")
        command = self.commands[command_list_view.index]
        self.push_screen(InfoScreen(command), self.maybe_delete_entry)

    def maybe_delete_entry(self, delete_entry):
        if delete_entry:
            self.delete_entry()

    def action_delete_entry(self):
        self.delete_entry()

    def delete_entry(self):
        command_list_view = self.get_child_by_id(id="command_list_view")
        index = command_list_view.index
        command = self.commands[index]

        # Delete from database
        engine = create_engine(self.database)
        with Session(engine) as session:
            delete_query = delete(ShellCommand).where(ShellCommand.id == command.id)
            session.execute(delete_query)
            session.commit()

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