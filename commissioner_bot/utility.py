import json


def write_json_data(file_path, new_data):
    """
    Write JSON data to a file.
    Args:
        file_path (str): The path to the JSON file to write to.
        new_data (dict): The new JSON data to write to the file.
    """
    # Open the JSON file in write mode
    with open(file_path, 'w') as json_file:
        # Write the new JSON data to the file
        json.dump(new_data, json_file, indent=4)

    print("JSON data written to the file:", new_data)


def read_json_data(file_path: str) -> dict:
    """
    Read JSON data from a file.
    :param file_path: str
    :return: dict
    """
    # Open and read the JSON file
    with open(file_path) as json_file:
        return json.load(json_file)