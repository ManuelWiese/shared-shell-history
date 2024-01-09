import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from model import ShellCommand


def main():
    """Entry point of the script.

    Parses command line arguments and inserts a command record into the
    database.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", type=str, required=True)
    parser.add_argument("--database", type=str, required=True)
    parser.add_argument("--host", type=str, required=True)
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--user", type=str, required=True)
    parser.add_argument("--venv", type=str, default=None)
    arguments = parser.parse_args()

    if arguments.venv == "":
        arguments.venv = None

    engine = create_engine(arguments.database)

    insert_command(
        engine,
        arguments.user,
        arguments.host,
        arguments.path,
        arguments.command,
        arguments.venv
    )


def insert_command(engine, user, host, path, command, venv):
    """Inserts a command into the database.

    Args:
        engine (Engine): SQLAlchemy engine object.
        user (str): User name.
        host (str): Host name.
        path (str): Path.
        command (str): Command.
        venv (str): Virtual environment.
    """
    with Session(engine) as session:
        new_command = ShellCommand(
            user_name=user,
            host=host,
            path=path,
            command=command,
            venv=venv
        )
        session.add(new_command)
        session.commit()


if __name__ == "__main__":
    main()
