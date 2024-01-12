import re

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button, Footer, Input,
    Label, ListItem, ListView, SelectionList
)

from sqlalchemy import create_engine, delete, desc, distinct, select
from sqlalchemy.orm import Session

from model import ShellCommand


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


class CommandHistory(App):
    CSS_PATH = "select_from_history.tcss"
    BINDINGS = [
        Binding("q", "quit()", "Quit", show=True),
        Binding("u", "select_user()", "Select User", show=True),
        Binding("h", "select_host()", "Select Host", show=True),
        Binding("i", "show_info()", "Show Info", show=True),
        Binding("d", "delete_entry()", "Delete Entry", show=True),
        Binding("s", "search", "Search", show=True),
    ]

    def __init__(self, database, tmp_file, user=None, host=None):
        """
        Initialize the CommandHistory instance.

        Args:
            database (str): The database connection string or path.
            tmp_file (str): The path to the temporary file for command storage.
            user (str, optional): User to initially filter the commands by.
            host (str, optional): Host to initially filter the commands by.
        """
        super().__init__()
        self.database = database
        self.tmp_file = tmp_file
        self.search_string = ""

        self.commands = self.fetch_commands()
        self.usernames = self.fetch_users()
        self.hosts = self.fetch_hosts()

        self.selected_usernames = self.usernames if user is None else [user]
        self.selected_hosts = self.hosts if host is None else [host]

        self.filtered_commands = self.get_filtered_commands()

    def fetch_users(self):
        """
        Fetch and return a list of distinct usernames from the database.

        Returns:
            list: A list of unique usernames.
        """
        return self.fetch_distinct_column_values(ShellCommand.user_name)

    def fetch_hosts(self):
        """
        Fetch and return a list of distinct hostnames from the database.

        Returns:
            list: A list of unique hostnames.
        """
        return self.fetch_distinct_column_values(ShellCommand.host)

    def fetch_distinct_column_values(self, column):
        """
        Fetch and return a list of distinct values from a specified column in the database.

        Args:
            column (Column): The SQLAlchemy Column object to fetch distinct values from.

        Returns:
            list: A list of distinct values from the specified column.
        """
        engine = create_engine(self.database)
        with Session(engine) as session:
            query = select(distinct(column))
            results = session.execute(query).all()
        return [result[0] for result in results]

    def fetch_commands(self):
        """
        Fetch and return all command entries from the database,
        ordered by their IDs in descending order.

        Returns:
            list: A list of ShellCommand objects representing the command entries.
        """
        engine = create_engine(self.database)
        with Session(engine) as session:
            query = select(ShellCommand).order_by(desc(ShellCommand.id))
            results = session.execute(query).all()

        return [result[0] for result in results]

    def get_filtered_commands(self):
        """
        Filter the command list based on selected usernames, hosts, and a search string.

        Returns:
            list: A list of filtered ShellCommand objects.
        """
        return [command for command in self.commands if self.command_matches_filters(command)]

    def command_matches_filters(self, command):
        """
        Check if a given command matches the selected filters.

        Args:
            command (ShellCommand): The command object to be checked.

        Returns:
            bool: True if the command matches the filters, False otherwise.
        """
        if not command.user_name in self.selected_usernames:
            return False

        if not command.host in self.selected_hosts:
            return False

        if self.search_string and not self.command_does_match(command.command):
            return False

        return True

    def command_does_match(self, command):
        """
        Check if the given command contains a match for the search string.

        This method uses regular expressions to search for the search string within 
        the command. The search is case-sensitive.

        Args:
            command (str): The command string to be searched.

        Returns:
            bool: True if the search string is found within the command, False otherwise.
        """
        match = re.search(self.search_string, command)
        return match is not None

    def compose(self) -> ComposeResult:
        """
        Compose the widgets to be displayed in the Textual app.

        This method sets up the main layout of the app, including a ListView for
        displaying command items, a StatusBar and a Footer.

        Yields:
            ComposeResult: The widgets to be displayed in the app layout.
        """
        list_items = self.get_list_items()
        yield ListView(*list_items, id="command_list_view")
        yield Label(
            self.get_status_string(),
            id="status_bar"
        )
        yield Footer()

    def get_list_items(self):
        """
        Generate a sequence of CommandListItem objects based on filtered commands.

        This method creates a CommandListItem for each command in `self.filtered_commands`.

        Returns:
            Generator[CommandListItem]: A generator yielding CommandListItem objects.
        """
        return (
            CommandListItem(command)
            for command in self.filtered_commands
        )

    def get_status_string(self):
        """
        Generate a status string that summarizes the current selections of users,
        hosts, and the search string.

        Returns:
            str: A string representing the current selections and search state.
        """
        strings = []

        if set(self.usernames) != set(self.selected_usernames):
            strings.append(
                f"Selected Users: [{', '.join(self.selected_usernames)}]"
            )
        else:
            strings.append("Selected Users: [*]")

        if set(self.hosts) != set(self.selected_hosts):
            strings.append(
                f"Selected Hosts: [{', '.join(self.selected_hosts)}]"
            )
        else:
            strings.append("Selected Hosts: [*]")

        if self.search_string:
            strings.append(
                f"Search String: {self.search_string}"
            )

        return ", ".join(strings)

    def on_list_view_selected(self, event: ListView.Selected):
        """
        Handle the event when an item is selected from the ListView.

        This method writes the selected command to a temporary file and then exits the application.

        Args:
            event (ListView.Selected): The selection event containing the selected item.
        """
        command = event.item.command.command
        with open(self.tmp_file, "w") as f:
            f.write(command)

        self.action_quit()

    def action_quit(self):
        """
        Exit the application.

        This method is typically bound to a quit action or command within the application.
        """
        exit()

    def action_select_user(self):
        """
        Trigger an action to select users.

        This method pushes a new SelectionScreen onto the application's screen stack.
        The SelectionScreen is configured to allow the user to select one or more usernames.
        Upon selection, `set_selected_users` is called to update the application state 
        with the selected usernames.
        """
        self.push_screen(
            SelectionScreen(
                "Select user(s)",
                self.usernames,
                self.selected_usernames
            ),
            self.set_selected_users
        )

    def set_selected_users(self, selected_usernames):
        """
        Set the selected users and update the views.

        Args:
            selected_usernames (list): The list of selected usernames.
        """
        self.selected_usernames = selected_usernames
        self.filtered_commands = self.get_filtered_commands()
        self.refresh_command_list_view()
        self.update_status_bar()

    def action_select_host(self):
        """
        Trigger an action to select hosts.

        This method pushes a new SelectionScreen onto the application's screen stack.
        The SelectionScreen is configured to allow the user to select one or more hosts.
        Upon selection, `set_selected_hosts` is called to update the application state 
        with the selected hosts.
        """
        self.push_screen(
            SelectionScreen(
                "Select host(s)",
                self.hosts,
                self.selected_hosts
            ),
            self.set_selected_hosts
        )

    def set_selected_hosts(self, selected_hosts):
        """
        Set the selected hosts and update the views.

        Args:
            selected_hosts (list): The list of selected hosts.
        """
        self.selected_hosts = selected_hosts
        self.filtered_commands = self.get_filtered_commands()
        self.refresh_command_list_view()
        self.update_status_bar()

    def refresh_command_list_view(self, index=0):
        """
        Refresh the command list view with updated list items and set the
        focus to a specific index.

        Args:
            index (int): The index of the item to be focused after refreshing.
                Defaults to 0.
        """
        command_list_view = self.get_child_by_id(id="command_list_view")
        command_list_view.clear()
        command_list_view.extend(self.get_list_items())
        command_list_view.index = index

    def update_status_bar(self):
        """
        Update the status bar with the current status string.
        """
        status_bar = self.get_child_by_id(id="status_bar")
        status_bar.update(self.get_status_string())

    def action_show_info(self):
        """
        Show detailed information about the selected command.

        This method retrieves the currently selected command from the command_list_view 
        and pushes an InfoScreen to display its details. It also sets maybe_delete_entry 
        as the callback to handle potential deletion of the command.
        """
        command_list_view = self.get_child_by_id(id="command_list_view")
        command = self.commands[command_list_view.index]
        self.push_screen(InfoScreen(command), self.maybe_delete_entry)

    def maybe_delete_entry(self, delete_entry):
        """
        Determine whether to delete the selected command entry.

        Args:
            delete_entry (bool): A flag indicating whether the entry should be deleted.
        """
        if delete_entry:
            self.delete_entry()

    def action_delete_entry(self):
        """
        Delete the currently selected command entry.
        This is typically bound to a key.
        """
        self.delete_entry()

    def delete_entry(self):
        """
        Delete the selected command from both the UI and the database.
        """
        command_list_view = self.get_child_by_id(id="command_list_view")
        index = command_list_view.index
        command = self.filtered_commands[index]

        self.delete_command_from_database(command)
        self.delete_command_from_lists(command)

        command_list_view.clear()
        command_list_view.extend(self.get_list_items())
        # select the item above the deleted item
        command_list_view.index = max(index - 1, 0)

    def delete_command_from_database(self, command):
        """
        Delete a command from the database.

        Args:
            command (ShellCommand): The command object to be deleted.
        """
        engine = create_engine(self.database)
        with Session(engine) as session:
            delete_query = delete(ShellCommand).where(
                ShellCommand.id == command.id)
            session.execute(delete_query)
            session.commit()

    def delete_command_from_lists(self, command):
        """
        Remove a command from the internal lists used in the application.

        Args:
            command (ShellCommand): The command object to be removed.
        """
        self.filtered_commands.remove(command)
        self.commands.remove(command)

    def action_search(self):
        """
        Initiate the action to perform a search.

        This method pushes a SearchScreen onto the application's screen stack,
        allowing the user to enter a search string. It sets change_search_string 
        as the callback to handle the update of the search string.
        """
        self.push_screen(
            SearchScreen(self.search_string),
            self.change_search_string
        )

    def change_search_string(self, new_search_string):
        if new_search_string == self.search_string:
            return

        self.search_string = new_search_string

        self.filtered_commands = self.get_filtered_commands()

        command_list_view = self.get_child_by_id(id="command_list_view")
        command_list_view.clear()
        command_list_view.extend(self.get_list_items())
        command_list_view.index = 0

        status_bar = self.get_child_by_id(id="status_bar")
        status_bar.update(self.get_status_string())


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
