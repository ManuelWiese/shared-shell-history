import argparse

from sqlalchemy import create_engine, MetaData

from table import define_table


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

    engine = create_engine(database_url)
    metadata = MetaData()

    bash_commands_table = define_table(metadata)
    bash_commands_table.create(engine, checkfirst=True)


if __name__ == "__main__":
    main()
