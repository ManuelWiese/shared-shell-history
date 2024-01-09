import argparse

from sqlalchemy import create_engine, Table, Column, String, Integer, TIMESTAMP, MetaData
from sqlalchemy.sql import func


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        type=str,
        required=True,
        help="Database URL"
    )
    args = parser.parse_args()

    database_url = args.database
    table_name = "bash_commands"

    engine = create_engine(database_url)
    metadata = MetaData()

    bash_commands_table = Table(
        table_name, metadata,
        Column('id', Integer, primary_key=True),
        Column('user_name', String, nullable=False),
        Column('host', String, nullable=False),
        Column('path', String, nullable=False),
        Column('venv', String, nullable=True),
        Column('command', String, nullable=False),
        Column('time', TIMESTAMP, server_default=func.current_timestamp())
    )

    bash_commands_table.create(engine, checkfirst=True)


if __name__ == "__main__":
    main()
