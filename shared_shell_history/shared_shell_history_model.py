from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, TIMESTAMP, func


Base = declarative_base()


class ShellCommand(Base):
    __tablename__ = 'bash_commands'
    id = Column(Integer, primary_key=True)
    user_name = Column(String)
    host = Column(String)
    path = Column(String)
    venv = Column(String, nullable=True)
    command = Column(String)
    time = Column(TIMESTAMP, server_default=func.current_timestamp())
