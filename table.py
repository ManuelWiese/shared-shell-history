from sqlalchemy import Table, Column, String, Integer, TIMESTAMP
from sqlalchemy.sql import func


def define_table(metadata):
    """Defines the table structure.

    Args:
        metadata (MetaData): SQLAlchemy MetaData instance.

    Returns:
        Table: SQLAlchemy Table object for 'bash_commands'.
    """
    return Table(
        'bash_commands', metadata,
        Column('id', Integer, primary_key=True),
        Column('user_name', String),
        Column('host', String),
        Column('path', String),
        Column('venv', String, nullable=True),
        Column('command', String),
        Column('time', TIMESTAMP, server_default=func.current_timestamp())
    )
