from commissioner_bot.network import send_discord_message
import json
# Open and read the JSON file
with open('commissioner_bot/json/players.json') as json_file:
    players = json.load(json_file)


add_string = "ADD ✅"
drop_string = "DROP 🔻"


def create_field(name: str, value: str, inline: bool = False):
    return {
        "name": name,
        "value": value,
        "inline": inline
    }


def post_free_agency_transaction(transaction: dict):
    """
    Post a free agency transaction to Discord.
    :param transaction: The transaction to post.
    """
    print(f"Posting free agency transaction: {transaction}")
    add = transaction['adds']
    drop = transaction['drops']
    team_id = transaction['roster_ids'][0]
    player_id = None
    if add is not None:
        player_id = list(add.keys())[0]
        add = players[player_id]
    if drop is not None:
        dropped_id = list(drop.keys())[0]
        drop = players[dropped_id]
        if add is None:
            player_id = dropped_id

    fields = []
    if add is not None:
        fields.append(create_field(add_string, add['full_name'], True))
    if drop is not None and add is not None:
        fields.append(create_field("", "", True))
    if drop is not None:
        fields.append(create_field(drop_string, drop['full_name'], True))

    discord_message = {
        "username": "Sleeper",
        "avatar_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw",
        "embeds": [
            {
                "author": {
                    "name": "Free Agency Pickup" if add else "Drop",
                    "icon_url": "https://sleepercdn.com/uploads/002cc07b558618b29d4479902721f662.jpg"
                },
                "title": f"The {team_id} have made a transaction!",
                "fields": fields,
                "thumbnail": {
                    "url": f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg" if player_id else None
                }
            }
        ]
    }

    send_discord_message(discord_message)


def post_waiver_claim_transaction(transaction: dict, failures: list = None):
    """
    Post a waiver claim transaction to Discord.
    :param transaction: The transaction to post.
    """
    print(f"Posting waiver claim transaction: {transaction}")
    add = transaction['adds']
    add_id = list(add.keys())[0]
    add = players[add_id]
    drop = transaction['drops']
    team_id = transaction['roster_ids'][0]
    if drop is not None:
        dropped_id = list(drop.keys())[0]
        drop = players[dropped_id]
        if add is None:
            player_id = dropped_id

    fields = [create_field(add_string, add['full_name'], True)]
    if drop is not None:
        fields.append(create_field("", "", True))
        fields.append(create_field(drop_string, drop['full_name'], True))

    fields.append(create_field("Budget Spent", f"${transaction['settings']['waiver_bid']}"))

    if failures is not None:
        failed_claims = ""
        for failure in failures:
            failed_claims += f"{failure['roster_ids'][0]}: ${failure['settings']['waiver_bid']}\n"
        fields.append(create_field("Failed Claims", failed_claims))

    discord_message = {
        "username": "Sleeper",
        "avatar_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw",
        "embeds": [
            {
                "author": {
                    "name": "Waiver Claim",
                    "icon_url": "https://sleepercdn.com/uploads/002cc07b558618b29d4479902721f662.jpg"
                },
                "title": f"The {team_id} have made a transaction!",
                "fields": fields,
                "thumbnail": {
                    "url": f"https://sleepercdn.com/content/nfl/players/{add_id}.jpg"
                }
            }
        ]
    }

    send_discord_message(discord_message)


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
            player = players[player_id]
            gets.append(player['full_name'])
    for player_id in drops:
        if drops[player_id] == team_id:
            player = players[player_id]
            gives.append(player['full_name'])
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
    transaction = sample_trade
    teams = transaction['roster_ids']
    fields = []
    for team in teams:
        fields.append(create_field(f"> {team}", ""))
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
                "title": " ↔️ ".join([str(team) for team in teams]),
                "fields": fields,
                "thumbnail": {
                    "url": "https://www.theshirtlist.com/wp-content/uploads/2022/11/Epic-Handshake.jpg"
                }
            }
        ]
    }

    send_discord_message(discord_message)

