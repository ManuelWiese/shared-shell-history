import curses
import argparse

from menu import Menu, CommandMenu


def main(stdscr):
    arguments = parse_arguments()
    menu = CommandMenu(stdscr, arguments.user, None, arguments.db_url,)
    selected_command = menu.display()

    selected_command = "" if selected_command is None else selected_command

    with open(arguments.tmp_file, "w") as f:
        f.write(selected_command)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db_url", type=str, required=True)
    parser.add_argument("--tmp_file", type=str, required=True)
    parser.add_argument("--user", type=str, default=None)
    return parser.parse_args()


# Run the program
if __name__ == "__main__":
    selected_command = curses.wrapper(main)