import curses
import argparse
import subprocess
import json

def main(stdscr):
    arguments = parse_arguments()
    commands = get_commands(
        arguments.db_url,
        user=arguments.user
    )
    selected_command = display(stdscr, commands)

    with open(arguments.tmp_file, "w") as f:
        f.write(selected_command)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_url", type=str, required=True)
    parser.add_argument("--tmp_file", type=str, required=True)
    parser.add_argument("--user", type=str, default=None)
    return parser.parse_args()


def get_commands(db_url, user=None, host=None): #None means any

    if user is None and host is None:
        where_clause = ""
    else:
        conditions = []
        if user is not None:
            conditions.append(f"user_name='{user}'")
        if host is not None:
            conditions.append(f"host='{host}'")
        where_clause = f" WHERE {' AND '.join(conditions)}"

    psql_command = (
        f"psql {db_url} -t -c"
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

    return commands


def display(stdscr, commands):
    # Turn off cursor blinking
    curses.curs_set(0)

    # Color scheme for selected row
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    # Specify the current selected row
    current_row = 0
    top_row = 0  # First row of the list displayed on screen
    search_string = ""


    # Initial display
    filtered_commands = commands
    print_menu(stdscr, current_row, filtered_commands, top_row)
    print_search_bar(stdscr, search_string)

    while True:
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
            if current_row < top_row:
                top_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(filtered_commands) - 1:
            current_row += 1
            if current_row >= top_row + stdscr.getmaxyx()[0]:
                top_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return commands[current_row]["command"]  # Return the selected command
        elif key == curses.KEY_BACKSPACE:
            search_string = search_string[:-1]
        elif key >= 32 and key <= 126:  # ASCII printable characters
            search_string += chr(key)
            current_row = 0

        # Update the display
        filtered_commands = filter_commands(commands, search_string)
        print_menu(stdscr, current_row, filtered_commands, top_row)
        print_search_bar(stdscr, search_string)


def print_menu(stdscr, selected_row_idx, commands, top_row):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    for idx, row in enumerate(commands[top_row:top_row+h]):
        x = 0
        y = idx
        if idx + top_row == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row_to_str(row))
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, row_to_str(row))
    stdscr.refresh()


def row_to_str(row):
    return f"{row['command']}"


def print_search_bar(stdscr, search_string):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 1, 0, "Search: " + search_string)
    stdscr.refresh()


def filter_commands(commands, search_string):
    return [command for command in commands if search_string.lower() in command["command"].lower()]


# Run the program
if __name__ == "__main__":
    selected_command = curses.wrapper(main)