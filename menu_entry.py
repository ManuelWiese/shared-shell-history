from abc import ABC
from abc import abstractmethod


class MenuEntry(ABC):
    @abstractmethod
    def __str__(self) -> str:
        ...


class Command(MenuEntry):
    def __init__(self, command, user_name, time, host) -> None:
        self.command = command
        self.user_name = user_name
        self.time = time
        self.host = host

    @classmethod
    def from_dict(cls, dictionary):
        return cls(**dictionary)

    def __str__(self) -> str:
        return f"{self.host} {self.command}"


class Host(MenuEntry):
    def __init__(self, host) -> None:
        self.host = host
    
    def __str__(self) -> str:
        return self.host


class User(MenuEntry):
    def __init__(self, username) -> None:
        self.username = username
    
    def __str__(self) -> str:
        return self.username