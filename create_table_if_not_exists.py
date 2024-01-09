import argparse

from sqlalchemy import create_engine

from model import Base


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
    Base.metadata.create_all(engine, checkfirst=True)


if __name__ == "__main__":
    main()
