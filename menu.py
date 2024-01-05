from abc import ABC, abstractmethod
import curses
import json
import subprocess
from typing import Optional, List

from menu_entry import Any, Command, Host, User, MenuEntry


KEY_ESCAPE = 27
KEY_NEWLINE = 10
KEY_CARRIAGE_RETURN = 13


class Menu(ABC):
    def __init__(self, stdscr, menu_entries, title=None) -> None:
        self.stdscr = stdscr
        self.menu_entries = menu_entries
        self.title = title
        self.top_row = 0
        self.current_row = 0
        self.search_string = ""
        self.spare_bottom_lines = 2
        self.spare_top_lines = 1 if self.title is not None else 0

        # Turn off cursor blinking
        curses.curs_set(0)

        # Color scheme for selected row
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def get_menu_entries(self) -> List[MenuEntry]:
        return [
            entry
            for entry in self.menu_entries
            if self.search_string.lower() in str(entry).lower()
        ]

    def display(self) -> Optional[str]:
        menu_entries = self.get_menu_entries()
        self.print_menu(menu_entries)
        self.print_search_bar()
        self.print_menu_bar()
        self.print_top_bar()
        while True:
            key = self.stdscr.getch()
            self.handle_navigation_input(key, len(menu_entries))
            self.handle_search_input(key)
            self.handle_special_input(key)

            if key in [KEY_NEWLINE, KEY_CARRIAGE_RETURN, curses.KEY_ENTER]:
                return menu_entries[self.current_row].get_return_value()
            if key in [curses.KEY_F1, KEY_ESCAPE]:
                return None

            menu_entries = self.get_menu_entries()
            self.print_menu(menu_entries)
            self.print_search_bar()
            self.print_menu_bar()
            self.print_top_bar()

    def handle_navigation_input(self, key, num_entries):
        if key == curses.KEY_UP and self.current_row > 0:
            self.current_row -= 1
            if self.current_row < self.top_row:
                self.top_row -= 1
        elif key == curses.KEY_DOWN and self.current_row < num_entries - 1 - self.spare_top_lines:
            self.current_row += 1
            if self.current_row >= self.top_row + self.stdscr.getmaxyx()[0] - self.spare_bottom_lines - self.spare_top_lines:
                self.top_row += 1
    
    def handle_search_input(self, key):
        if key == curses.KEY_BACKSPACE:
            self.search_string = self.search_string[:-1]
        elif key >= 32 and key <= 126:  # ASCII printable characters
            self.search_string += chr(key)
            self.current_row = 0

    def handle_special_input(self, key):
        pass

    def print_menu(self, menu_entries) -> None:
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        for idx, entry in enumerate(menu_entries[self.top_row:self.top_row+h-self.spare_bottom_lines-self.spare_top_lines]):
            x = 0
            y = idx + self.spare_top_lines
            if idx + self.top_row == self.current_row:
                self.stdscr.attron(curses.color_pair(1))
                self.stdscr.addstr(y, x, self.entry_to_string(entry))
                self.stdscr.attroff(curses.color_pair(1))
            else:
                self.stdscr.addstr(y, x, self.entry_to_string(entry))
        self.stdscr.refresh()

    def entry_to_string(self, entry):
        return entry.to_string()

    def print_search_bar(self) -> None:
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 2, 0, "Search: " + self.search_string)
        self.stdscr.refresh()

    def print_menu_bar(self) -> None:
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 1, 0, "F1 - Exit | Enter - Select entry | ↑/↓ - Navigate up/down")
        self.stdscr.refresh()

    def print_top_bar(self) -> None:
        if self.title is None:
            return
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(0, 0, self.title, curses.A_UNDERLINE | curses.A_BOLD)
        self.stdscr.refresh()


class CommandMenu(Menu):
    def __init__(self, stdscr, username, host, db_url) -> None:
        self.username = username
        self.host = host
        self.db_url = db_url

        menu_entries = self.get_command_menu_entries()

        super().__init__(stdscr, menu_entries)

        self.spare_top_lines = 1

    def get_command_menu_entries(self): #None means any
        if self.username is None and self.host is None:
            where_clause = ""
        else:
            conditions = []
            if self.username is not None:
                conditions.append(f"user_name='{self.username}'")
            if self.host is not None:
                conditions.append(f"host='{self.host}'")
            where_clause = f" WHERE {' AND '.join(conditions)}"

        psql_command = (
            f"psql {self.db_url} -t -c"
            f"\"SELECT to_json(t) FROM"
            f"(SELECT user_name, host, time, command FROM bash_commands{where_clause}) AS t\""
        )

        process = subprocess.run(
            psql_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        commands = reversed(process.stdout.splitlines())
        commands = [command for command in commands if command]
        commands = [json.loads(command) for command in commands]
        for command in commands:
            command["command"] = command["command"].strip()

        return [Command.from_dict(command) for command in commands]

    def handle_special_input(self, key):
        if key == curses.KEY_F2:
            user_menu_entries = self.get_user_menu_entries()
            user_menu = Menu(
                self.stdscr,
                user_menu_entries,
                title="Select User"
            )

            self.username = user_menu.display()
            self.menu_entries = self.get_command_menu_entries()
        if key == curses.KEY_F3:
            host_menu_entries = self.get_host_menu_entries()
            host_menu = Menu(
                self.stdscr,
                host_menu_entries,
                title="Select Host"
            )

            self.host = host_menu.display()
            self.menu_entries = self.get_command_menu_entries()
        
    def get_user_menu_entries(self):
        psql_command = (
            f"psql {self.db_url} -t -c "
            f"\"SELECT DISTINCT(user_name) FROM bash_commands\""
        )

        process = subprocess.run(
            psql_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        user_names = process.stdout.splitlines()
        return [Any()] + [User(username.strip()) for username in user_names]

    def get_host_menu_entries(self):
        psql_command = (
            f"psql {self.db_url} -t -c "
            f"\"SELECT DISTINCT(host) FROM bash_commands\""
        )

        process = subprocess.run(
            psql_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        hosts = process.stdout.splitlines()
        return [Any()] + [Host(host.strip()) for host in hosts]

    def print_menu_bar(self) -> None:
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h - 1, 0, "F1 - Exit | F2 - Select user | F3 - Select host | Enter - Select entry | ↑/↓ - Navigate up/down")
        self.stdscr.refresh()

    def print_top_bar(self) -> None:
        h, w = self.stdscr.getmaxyx()

        user = self.username if self.username is not None else "Any"
        host = self.host if self.host is not None else "Any"

        self.stdscr.addstr(
            0,
            0,
            f"Select command(filtered by User={user},Host={host})",
            curses.A_UNDERLINE | curses.A_BOLD
        )
        self.stdscr.refresh()

    def entry_to_string(self, entry):
        return entry.to_string(
            show_user_name=self.username is None,
            show_host=self.host is None,
            show_time=False
        )