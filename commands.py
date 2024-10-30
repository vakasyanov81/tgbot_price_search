from enum import Enum


class Commands(Enum):
    DOWNLOAD_PRICE = 1


class CommandStateStore:

    def __init__(self):
        self.current_command = {}

    def set_command(self, user_id: int, cmd: Commands):
        if not isinstance(cmd, Commands):
            raise "Wrong type command!"
        self.current_command[user_id] = cmd

    def current_state(self, user_id):
        return self.current_command.get(user_id)

    def clear(self, user_id):
        self.current_command[user_id] = None
