import os
import json
import time

from langgraph.checkpoint.memory import MemorySaver


def is_json_file(file_path: str = "./tracked.json") -> bool:
    """checks if json file exists"""
    return os.path.exists(file_path)


def save_to_json(
        data_to_save, file_path: str = "./tracked.json") -> None:
    """saves data to a json file"""
    existing_data = load_from_json(file_path)
    existing_data.extend(data_to_save)

    # handle
    with open(file_path, "w") as data_file:
        json.dump(existing_data, data_file, indent=4)


def load_from_json(file_path: str = "./tracked.json") -> list:
    """loads data from a json file"""
    retrieved_data: list = []

    if is_json_file(file_path):
        with open(file_path, "r") as data_file:
            # read from an existing json file

            try:
                # handle
                # parse existing data in json file
                retrieved_data = json.load(data_file)
            except Exception:
                # returns an empty list if file is empty
                retrieved_data = []

    else:
        # handle
        with open(file_path, "w") as data_file:
            save_to_json([], file_path)

    return retrieved_data


class ExpiringMemorySaver(MemorySaver):
    def __init__(self, inactivity_ttl: int):
        super().__init__()
        self.last_access = {}
        self.inactivity_ttl = inactivity_ttl

    # def put(self, thread_id, state):
    #     super().put(thread_id, state)
    #     self.last_access[thread_id] = time()

    # def get(self, thread_id):
    #     state = super().get(thread_id)
    #     if state is not None:
    #         self.last_access[thread_id] = time()
    #     return state

    def put(self, *args, **kwargs):
        """Accept any arguments and pass to parent"""
        result = super().put(*args, **kwargs)

        # Try to extract thread_id from first argument (config)
        if args and isinstance(args[0], dict):
            config = args[0]
            thread_id = config.get("configurable", {}).get(
                "thread_id", "default")
            self.last_access[thread_id] = time.time()

        return result

    def get_tuple(self, config: dict):
        """Track access on retrieval"""
        result = super().get_tuple(config)

        if result is not None:
            thread_id = config.get("configurable", {}).get(
                "thread_id", "default")
            self.last_access[thread_id] = time.time()

        return result

    def cleanup(self):
        now = time.time()
        expired = [
            tid for tid, ts in self.last_access.items()
            if now - ts > self.inactivity_ttl]
        for tid in expired:
            self.storage.pop(tid, None)
            self.last_access.pop(tid, None)

        return len(expired)

    def get_active_sessions(self):
        """Get count of currently active sessions"""
        return len(self.last_access)
