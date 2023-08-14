import json

team_colors = {
    'ARI': "97233F",
    'ATL': "A71930",
    'BAL': "241773",
    'BUF': "00338D",
    'CAR': "0085CA",
    'CHI': "0B162A",
    'CIN': "FB4F14",
    'CLE': "311D00",
    'DAL': "041E42",
    'DEN': "FB4F14",
    'DET': "0076B6",
    'GB': "203731",
    'HOU': "03202F",
    'IND': "002C5F",
    'JAX': "006778",
    'KC': "E31837",
    'LV': "000000",
    'LAC':"0080C6",
    'LAR': "003594",
    'MIA': "008E97",
    'MIN': "4F2683",
    'NE': "002244",
    'NO': "D3BC8D",
    'NYG': "0B2265",
    'NYJ': "125740",
    'PHI': "004C54",
    'PIT': "FFB612",
    'SF': "AA0000",
    'SEA': "69BE28",
    'TB': "D50A0A",
    'TEN': "0C2340",
    'WAS': "773141"
}


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