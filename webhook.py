from network import send_discord_message
import json
# Open and read the JSON file
with open('players.json') as json_file:
    players = json.load(json_file)

sample_trade = {
    "waiver_budget": [],
    "type": "trade",
    "transaction_id": "702990758956855296",
    "status_updated": 1621988437145,
    "status": "complete",
    "settings": None,
    "roster_ids": [
        11,
        4
    ],
    "metadata": None,
    "leg": 1,
    "drops": {
        "6886": 11,
        "1426": 4
    },
    "draft_picks": [
        {
            "season": "2021",
            "round": 1,
            "roster_id": 11,
            "previous_owner_id": 11,
            "owner_id": 4,
            "league_id": None
        },
        {
            "season": "2021",
            "round": 3,
            "roster_id": 11,
            "previous_owner_id": 11,
            "owner_id": 4,
            "league_id": None
        },
        {
            "season": "2021",
            "round": 1,
            "roster_id": 4,
            "previous_owner_id": 4,
            "owner_id": 11,
            "league_id": None
        }
    ],
    "creator": "458459116440907776",
    "created": 1621968567173,
    "consenter_ids": [
        11,
        4
    ],
    "adds": {
        "6886": 4,
        "1426": 11
    }
}

sample_drop = {
    "waiver_budget": [],
    "type": "free_agent",
    "transaction_id": "702990280529354752",
    "status_updated": 1621968453107,
    "status": "complete",
    "settings": None,
    "roster_ids": [
        4
    ],
    "metadata": None,
    "leg": 1,
    "drops": {
        "6996": 4
    },
    "draft_picks": [],
    "creator": "458459116440907776",
    "created": 1621968453107,
    "consenter_ids": [
        4
    ],
    "adds": None
}

sample_completed_waiver_claim = {
    "waiver_budget": [],
    "type": "waiver",
    "transaction_id": "748834206360137728",
    "status_updated": 1632899075079,
    "status": "complete",
    "settings": {
        "waiver_bid": 1,
        "seq": 1
    },
    "roster_ids": [
        1
    ],
    "metadata": {
        "notes": "Your waiver claim was processed successfully!"
    },
    "leg": 3,
    "drops": {
        "6849": 1
    },
    "draft_picks": [],
    "creator": "460107869405048832",
    "created": 1632898496764,
    "consenter_ids": [
        1
    ],
    "adds": {
        "7694": 1
    }
}

sample_failed_waiver_claim = {
    "waiver_budget": [],
    "type": "waiver",
    "transaction_id": "746206443874746368",
    "status_updated": 1632294308959,
    "status": "failed",
    "settings": {
        "waiver_bid": 5,
        "seq": 3
    },
    "roster_ids": [
        7
    ],
    "metadata": {
        "notes": "This player was claimed by another owner."
    },
    "leg": 2,
    "drops": None,
    "draft_picks": [],
    "creator": "460209843869839360",
    "created": 1632271989366,
    "consenter_ids": [
        7
    ],
    "adds": {
        "1535": 7
    }
}

sample_complete_free_agent_claim = {
    "waiver_budget": [],
    "type": "free_agent",
    "transaction_id": "743801547095474176",
    "status_updated": 1631698617293,
    "status": "complete",
    "settings": None,
    "roster_ids": [
        4
    ],
    "metadata": None,
    "leg": 2,
    "drops": {
        "3209": 4
    },
    "draft_picks": [],
    "creator": "458459116440907776",
    "created": 1631698617293,
    "consenter_ids": [
        4
    ],
    "adds": {
        "5284": 4
    }
}

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

