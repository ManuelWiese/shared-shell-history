import re

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Label, ListView, ListItem

from sqlalchemy import create_engine, delete, desc, distinct, select
from sqlalchemy.orm import Session

from .command_list_item import CommandListItem
from .info_screen import InfoScreen
from .search_screen import SearchScreen
from .selection_screen import SelectionScreen

from shared_shell_history_model import ShellCommand


class LazyLoadingListView(ListView):
    """
    A ListView that loads items lazily.

    This ListView subclass is designed
    to load items lazily in batches. It extends the ListView class
    and overrides the `watch_index` method to load more items when the
    index is changed.

    Attributes:
        _full_children (list): A list of all items to be loaded.
        _batch_size (int): The number of items to load in each batch.
    """
    def __init__(
        self,
        *children: ListItem,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        batch_size: int = 64
    ) -> None:
        self._full_children = children
        self._batch_size = batch_size

        super().__init__(
            *children[:2 * self._batch_size],
            initial_index=initial_index,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled
        )

    @property
    def _loaded_items(self):
        """
        The number of items that have been loaded so far.
        """
        return len(self._nodes)

    def watch_index(self, old_index: int | None, new_index: int | None) -> None:
        """
        Watch the index change and load more items if necessary.

        This method is called when the index changes, and it determines
        whether more items need to be loaded based on the new index.

        Args:
            old_index (int): The previous index.
            new_index (int): The new index.
        """
        # Load more items if the new index is valid in the sense
        # that it is within the range of the full children list.
        if new_index is not None and new_index >= 0 and new_index < len(self._full_children):
            if new_index > self._loaded_items:
                # Load enough batches to reach the new index plus at least one more batch
                num_batches_to_load = (new_index - self._loaded_items) // self._batch_size + 2
            elif new_index > self._loaded_items - self._batch_size:
                num_batches_to_load = 1
            else:
                num_batches_to_load = 0

            self._load_batches(num_batches_to_load)

        super().watch_index(
            old_index,
            new_index
        )

    def _load_batches(self, number_of_batches):
        """
        Load a specified number of batches of items.

        This method loads a specified number of batches of items
        from the `_full_children` list. The items are appended to the
        existing list of items in the ListView.

        Args:
            number_of_batches (int): The number of batches to load.
        """
        if self._loaded_items >= len(self._full_children):
            return

        items_to_load = self._full_children[
            self._loaded_items:self._loaded_items + number_of_batches * self._batch_size
        ]

        super().extend(
            items_to_load
        )

    def clear(self):
        """
        Clear the list view and reset the full children list.
        """
        self._full_children = []
        return super().clear()

    def extend(self, items):
        """
        Extend the list view with new items.

        This method extends the list view with new items. If the list view
        is not empty, it raises a NotImplementedError. The case of non-empty
        list views is not needed here so far.

        Args:
            items (list): A list of items to be added to the list view.
        """
        if len(self._full_children) != 0:
            raise NotImplementedError(
                "extend was only implemented for the empty LazyLoadingListView."
            )

        self._full_children.extend(items)
        items_to_load = self._full_children[:2 * self._batch_size]

        return super().extend(
            items_to_load
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
        yield LazyLoadingListView(*list_items, id="command_list_view")
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
                f"Selected Users: \[{', '.join(self.selected_usernames)}]"
            )
        else:
            strings.append("Selected Users: [*]")

        if set(self.hosts) != set(self.selected_hosts):
            strings.append(
                f"Selected Hosts: \[{', '.join(self.selected_hosts)}]"
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
        self.log("START #############################################")
        command_list_view = self.get_child_by_id(id="command_list_view")
        self.log("BEFORE CLEAR #############################################")
        command_list_view.clear()
        self.log("LIST CLEARED #############################################")
        command_list_view.extend(self.get_list_items())
        self.log("LIST EXTENDED #############################################")
        command_list_view.index = index
        self.log("INDEX SET #############################################")

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

        # Refresh the command list view and adjust the selection
        new_index = max(index - 1, 0)  # select the item above the deleted item
        self.refresh_command_list_view(new_index)

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
        """
        Update the search string and refresh the application view.

        Args:
            new_search_string (str): The new search string input by the user.
        """
        if new_search_string == self.search_string:
            return

        self.search_string = new_search_string
        self.filtered_commands = self.get_filtered_commands()

        self.refresh_command_list_view()

        self.update_status_bar()
