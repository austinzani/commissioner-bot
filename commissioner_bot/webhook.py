from commissioner_bot.network import send_discord_message
from commissioner_bot.utility import read_json_data, team_colors


players = read_json_data('commissioner_bot/json/players.json')
add_string = "ADD ✅"
drop_string = "DROP 🔻"
sleeper_logo_url = "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw"


def create_field(name: str, value: str, inline: bool = False):
    return {
        "name": name,
        "value": value,
        "inline": inline
    }


def parse_team_object(team: dict) -> tuple:
    team_name = team.get('team_name')
    team_username = team.get('display_name')
    team_string = f"{team_name} ({team_username})" if team_name is not None else team_username

    avatar_string = team['avatar']
    if avatar_string is None:
        avatar_string = sleeper_logo_url

    return team_string, avatar_string


def parse_player_object(player_id: str) -> tuple:
    """
    Get the name of a player by their ID.
    :param player_id: The ID of the player.
    :return: The name of the player.
    """
    player = players[player_id]

    if player is None:
        return "Unknown Player", None, None
    team = player.get('team')
    team_color = team_colors[team] if team in team_colors else None
    if player['position'] == 'DEF':
        return f"{player['team']} DEF", f"https://sleepercdn.com/images/team_logos/nfl/{player['team'].lower()}.png", team_color
    return f"{player['full_name']}: ({player['position']})", f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg", team_color


def post_free_agency_transaction(transaction: dict):
    """
    Post a free agency transaction to Discord.
    :param transaction: The transaction to post.
    """
    print(f"Posting free agency transaction: {transaction}")
    add = transaction['adds']
    drop = transaction['drops']
    team_id = transaction['roster_ids'][0]
    if add is not None:
        add = list(add.keys())[0]
    if drop is not None:
        drop = list(drop.keys())[0]

    fields = []
    thumbnail_url = None
    team_color = None
    if add is not None:
        add_name, thumbnail_url, team_color = parse_player_object(add)
        fields.append(create_field(add_string, add_name, True))
    if drop is not None and add is not None:
        fields.append(create_field("", "", True))
    if drop is not None:
        drop_name, drop_url, drop_color = parse_player_object(drop)
        fields.append(create_field(drop_string, drop_name, True))
        if thumbnail_url is None:
            thumbnail_url = drop_url
        if team_color is None:
            team_color = drop_color

    users = read_json_data('commissioner_bot/json/users.json')
    team_object = users[str(team_id)]
    team_name, avatar_url = parse_team_object(team_object)

    discord_message = {
        "username": "Sleeper",
        "avatar_url": sleeper_logo_url,
        "embeds": [
            {
                "author": {
                    "name": "Free Agency Pickup" if add else "Drop",
                    "icon_url": avatar_url
                },
                "title": team_name,
                "color": int(team_color, 16) if team_color else None,
                "fields": fields,
                "thumbnail": {
                    "url": thumbnail_url
                }
            }
        ]
    }

    return send_discord_message(discord_message)


def post_waiver_claim_transaction(transaction: dict, failures: list = None):
    """
    Post a waiver claim transaction to Discord.
    :param failures: dictionary of failed transactions tied to the same waiver claim
    :param transaction: The transaction to post.
    """
    print(f"Posting waiver claim transaction: {transaction}")
    add = transaction['adds']
    add = list(add.keys())[0]
    drop = transaction['drops']
    team_id = transaction['roster_ids'][0]
    if drop is not None:
        drop = list(drop.keys())[0]

    add_name, thumbnail_url, team_color = parse_player_object(add)
    fields = [create_field(add_string, add_name, True)]
    if drop is not None:
        fields.append(create_field("", "", True))
        drop_name, drop_url, _ = parse_player_object(drop)
        fields.append(create_field(drop_string, drop_name, True))

    fields.append(create_field("Budget Spent", f"${transaction['settings']['waiver_bid']}"))

    users = read_json_data('commissioner_bot/json/users.json')
    if failures is not None:
        failure_map = {}
        # Loop through the failures and find the highest bid for each team
        for failure in failures:
            failed_roster_id = failure['roster_ids'][0]
            amount = failure['settings']['waiver_bid']
            if failed_roster_id not in failure_map or failure_map[failed_roster_id] < amount:
                failure_map[failed_roster_id] = amount
        failed_claims = ""
        for failed_roster_id in failure_map:
            team = users[str(failed_roster_id)]
            username = team.get('display_name')
            failed_claims += f"{username}: ${failure_map[failed_roster_id]}\n"
        if failed_claims != "":
            fields.append(create_field("Failed Claims", failed_claims))

    team_object = users[str(team_id)]
    team_name, avatar_url = parse_team_object(team_object)

    discord_message = {
        "username": "Sleeper",
        "avatar_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw",
        "embeds": [
            {
                "author": {
                    "name": "Waiver Claim",
                    "icon_url": avatar_url
                },
                "title": team_name,
                "color": int(team_color, 16) if team_color else None,
                "fields": fields,
                "thumbnail": {
                    "url": thumbnail_url
                }
            }
        ]
    }

    return send_discord_message(discord_message)


def parse_draft_pick(pick: dict):
    return f"{pick['season']} Round {pick['round']} (Team {pick['previous_owner_id']})"


def parse_trade_for_team(transaction: dict, team_id: int) -> tuple:
    """
    Parse a trade transaction for a given team.
    :param transaction: The transaction to parse.
    :param team_id: The team ID to parse for.
    """
    adds = transaction['adds']
    drops = transaction['drops']
    draft_picks = transaction['draft_picks']
    budget = transaction['waiver_budget']
    gives = []
    gets = []
    for player_id in adds:
        if adds[player_id] == team_id:
            player_name, _, _ = parse_player_object(player_id)
            gets.append(player_name)
    for player_id in drops:
        if drops[player_id] == team_id:
            player_name, _, _ = parse_player_object(player_id)
            gives.append(player_name)
    for draft_pick in draft_picks:
        if draft_pick['owner_id'] == team_id:
            gives.append(parse_draft_pick(draft_pick))
        elif draft_pick['previous_owner_id'] == team_id:
            gets.append(parse_draft_pick(draft_pick))
    for budget_transaction in budget:
        if budget_transaction['receiver'] == team_id:
            gets.append(f"${budget_transaction['amount']} FAB (from {budget_transaction['sender']})")
        elif budget_transaction['sender'] == team_id:
            gives.append(f"${budget_transaction['amount']} FAB (to {budget_transaction['receiver']})")

    return gives, gets


def post_trade(transaction: dict):
    """
    Post a trade transaction to Discord.
    :param transaction: The transaction to post.
    """
    print(f"Posting trade transaction: {transaction}")
    # Get the array of the team IDs involved in the trade
    teams = transaction['roster_ids']
    fields = []
    users = read_json_data('commissioner_bot/json/users.json')
    for team in teams:
        team_object = users[str(team)]
        team_name, _ = parse_team_object(team_object)
        fields.append(create_field(f"> {team_name}", ""))
        gives, gets = parse_trade_for_team(transaction, team)
        fields.append(create_field("Gives ➡️️", "\n".join(gives), True))
        fields.append(create_field("", "", True))
        fields.append(create_field("Gets ⬅️", "\n".join(gets), True))

    discord_message = {
        "username": "Sleeper",
        "avatar_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw",
        "embeds": [
            {
                "author": {
                    "name": "Trade",
                    "icon_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw"
                },
                "title": " ↔️ ".join([users[str(team)]['display_name'] for team in teams]),
                "fields": fields,
                "thumbnail": {
                    "url": "https://www.theshirtlist.com/wp-content/uploads/2022/11/Epic-Handshake.jpg"
                }
            }
        ]
    }

    return send_discord_message(discord_message)
