import os
import json


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
