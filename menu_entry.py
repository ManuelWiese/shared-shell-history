from abc import ABC
from abc import abstractmethod


class MenuEntry(ABC):
    @abstractmethod
    def __str__(self) -> str:
        ...

    @abstractmethod
    def get_return_value(self) -> str:
        ...

    def to_string(self, **kwargs)-> str:
        return str(self)


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
        return f"{self.command}"
    
    def to_string(self, show_user_name=True, show_host=True, show_time=True):
        repr_length = 10
        user_name_repr = f"{self.user_name[:repr_length]:<{repr_length}}" if show_user_name else ""
        host_repr = f"{self.host[:repr_length]:<{repr_length}}" if show_host else ""
        time_repr = f"{self.time[:repr_length]:<{repr_length}}" if show_time else ""
        command_repr = self.command

        values = [user_name_repr, host_repr, time_repr, command_repr]
        values = [value for value in values if value]

        return " | ".join(values)

    def get_return_value(self) -> str:
        return self.command


class Host(MenuEntry):
    def __init__(self, host) -> None:
        self.host = host
    
    def __str__(self) -> str:
        return self.host
    
    def get_return_value(self) -> str:
        return self.host


class User(MenuEntry):
    def __init__(self, username) -> None:
        self.username = username
    
    def __str__(self) -> str:
        return self.username

    def get_return_value(self) -> str:
        return self.username


class Any(MenuEntry):
    def __str__(self) -> str:
        return "Any"

    def get_return_value(self) -> str:
        return None