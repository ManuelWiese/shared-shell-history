import argparse

from sqlalchemy import create_engine, MetaData

from table import define_table


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
    metadata = MetaData()
    bash_commands_table = define_table(metadata)
    metadata.create_all(engine)

    insert_command(
        engine,
        bash_commands_table,
        arguments.user,
        arguments.host,
        arguments.path,
        arguments.command,
        arguments.venv
    )


def insert_command(engine, table, user, host, path, command, venv):
    """Inserts a command into the database.

    Args:
        engine (Engine): SQLAlchemy engine object.
        table (Table): SQLAlchemy table object.
        user (str): User name.
        host (str): Host name.
        path (str): Path.
        command (str): Command.
        venv (str): Virtual environment.
    """
    with engine.connect() as conn:
        insert_stmt = table.insert().values(
            user_name=user,
            host=host,
            path=path,
            command=command,
            venv=venv
        )
        conn.execute(insert_stmt)
        conn.commit()


if __name__ == "__main__":
    main()
