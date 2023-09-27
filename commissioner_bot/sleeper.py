from commissioner_bot.network import send_request_with_retries
from commissioner_bot.utility import team_colors
from commissioner_bot.discord_bot import Discord, add_string, drop_string
from commissioner_bot.mongodb import MongoCollection, db, player_collection, manager_collection


sleeper_logo_url = "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw"


class Sleeper:
    def __init__(self, league_id: str, discord: Discord):
        self.league_id = league_id
        self.league = MongoCollection(db, league_id)
        self.discord = discord

    @staticmethod
    def get_nfl_state():
        return send_request_with_retries('https://api.sleeper.app/v1/state/nfl')

    @staticmethod
    def get_nfl_players():
        return send_request_with_retries('https://api.sleeper.app/v1/players/nfl')

    @staticmethod
    def get_user_from_username(username):
        return send_request_with_retries(f'https://api.sleeper.app/v1/user/{username}')

    @staticmethod
    def get_leagues_from_user(user_id, year):
        return send_request_with_retries(f'https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{year}')

    def get_league_users(self):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/users')

    def get_league_transactions(self, week):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/transactions/{week}')

    def get_league_rosters(self):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/rosters')

    @staticmethod
    def update_players():
        success, players = Sleeper.get_nfl_players()
        if success:
            for player in players:
                player_object = players[player]
                player_object['_id'] = player
                player_collection.insert(player_object)
        else:
            print('Failed to update players')

    @staticmethod
    def get_player(player_id):
        return player_collection.get({"_id": player_id})

    def update_league_managers(self):
        success, users = self.get_league_users()
        if not success:
            print('Failed to update managers. Could not fetch league users.')
            return
        success, rosters = self.get_league_rosters()
        if not success:
            print('Failed to update managers. Could not fetch league rosters.')
            return
        updated_users = {}
        for user in users:
            # Find the roster associated with the user
            for roster in rosters:
                if roster['owner_id'] == user['user_id']:
                    team_id = roster['roster_id']
                    updated_users[str(team_id)] = {
                        'team_name': user['metadata'].get('team_name', None),
                        'avatar': user['metadata'].get('avatar', None),
                        'display_name': user.get('display_name', None)
                    }
                    break
        manager_collection.insert({"league_id": self.league_id, "users": updated_users})

    def get_league_managers(self):
        result = manager_collection.get({"league_id": self.league_id})
        return result['users'] if result is not None else None

    async def process_transactions(self, week):
        success, transactions = self.get_league_transactions(week)
        for transaction in transactions:
            transaction_id = transaction['transaction_id']

            # Check to see if the transaction has already been processed
            db_transactions = self.league.get({"transaction_id": transaction_id})
            if db_transactions is not None:
                print('already processed')
                continue

            status = transaction['status']
            success = False
            if status == 'failed':  # We don't care about failed transactions
                continue
            if transaction['type'] == 'waiver':
                player_id = list(transaction.get('adds').keys())[0]
                failed = []
                for t in transactions:
                    if t['type'] == 'waiver':
                        if t['status'] == 'failed':
                            if player_id in t['adds'] and t['status_updated'] == transaction['status_updated']:
                                failed.append(t)
                success = await self.process_waiver_claim_transaction(transaction, failed)
            elif transaction['type'] == 'trade':
                success = await self.process_trade(transaction)
            elif transaction['type'] == 'free_agent':
                success = await self.process_free_agency_transaction(transaction)
            if success:
                self.league.insert({"transaction_id": transaction_id, "status": "processed", "league_id": self.league_id})

    @staticmethod
    def parse_team_object(team: dict) -> tuple:
        team_name = team.get('team_name')
        team_username = team.get('display_name')
        team_string = f"{team_name} ({team_username})" if team_name is not None else team_username

        avatar_string = team['avatar']
        if avatar_string is None:
            avatar_string = sleeper_logo_url

        return team_string, avatar_string

    @staticmethod
    def parse_draft_pick(pick: dict):
        return f"{pick['season']} Round {pick['round']} (Team {pick['previous_owner_id']})"

    def parse_player_object(self, player_id: str) -> tuple:
        """
        Get the name of a player by their ID.
        :param player_id: The ID of the player.
        :return: The name of the player.
        """
        player = self.get_player(player_id)

        if player is None:
            return "Unknown Player", None, None
        team = player.get('team')
        team_color = team_colors[team] if team in team_colors else None
        if player['position'] == 'DEF':
            return f"{player['team']} DEF", f"https://sleepercdn.com/images/team_logos/nfl/{player['team'].lower()}.png", team_color
        return f"{player['full_name']}: ({player['position']})", f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg", team_color

    async def process_free_agency_transaction(self, transaction: dict):
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
            add_name, thumbnail_url, team_color = self.parse_player_object(add)
            fields.append(self.discord.create_field(add_string, add_name, True))
        if drop is not None and add is not None:
            fields.append(self.discord.create_field("", "", True))
        if drop is not None:
            drop_name, drop_url, drop_color = self.parse_player_object(drop)
            fields.append(self.discord.create_field(drop_string, drop_name, True))
            if thumbnail_url is None:
                thumbnail_url = drop_url
            if team_color is None:
                team_color = drop_color

        users = self.get_league_managers()
        team_object = users[str(team_id)]
        team_name, avatar_url = self.parse_team_object(team_object)

        return await self.discord.post_free_agency_transaction(team_name, avatar_url, thumbnail_url, team_color, fields, add is not None)

    async def process_waiver_claim_transaction(self, transaction: dict, failures: list = None):
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

        add_name, thumbnail_url, team_color = self.parse_player_object(add)
        fields = [self.discord.create_field(add_string, add_name, True)]
        if drop is not None:
            fields.append(self.discord.create_field("", "", True))
            drop_name, drop_url, _ = self.parse_player_object(drop)
            fields.append(self.discord.create_field(drop_string, drop_name, True))

        fields.append(self.discord.create_field("Budget Spent", f"${transaction['settings']['waiver_bid']}"))

        users = self.get_league_managers()
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
                fields.append(self.discord.create_field("Failed Claims", failed_claims))

        team_object = users[str(team_id)]
        team_name, avatar_url = self.parse_team_object(team_object)

        return await self.discord.post_waiver_claim_transaction(team_name, avatar_url, thumbnail_url, team_color, fields)

    def parse_trade_for_team(self, transaction: dict, team_id: int) -> tuple:
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
                player_name, _, _ = self.parse_player_object(player_id)
                gets.append(player_name)
        for player_id in drops:
            if drops[player_id] == team_id:
                player_name, _, _ = self.parse_player_object(player_id)
                gives.append(player_name)
        for draft_pick in draft_picks:
            if draft_pick['owner_id'] == team_id:
                gives.append(self.parse_draft_pick(draft_pick))
            elif draft_pick['previous_owner_id'] == team_id:
                gets.append(self.parse_draft_pick(draft_pick))
        for budget_transaction in budget:
            if budget_transaction['receiver'] == team_id:
                gets.append(f"${budget_transaction['amount']} FAB (from {budget_transaction['sender']})")
            elif budget_transaction['sender'] == team_id:
                gives.append(f"${budget_transaction['amount']} FAB (to {budget_transaction['receiver']})")

        return gives, gets

    async def process_trade(self, transaction: dict):
        """
        Post a trade transaction to Discord.
        :param transaction: The transaction to post.
        """
        print(f"Posting trade transaction: {transaction}")
        # Get the array of the team IDs involved in the trade
        teams = transaction['roster_ids']
        fields = []
        users = self.get_league_managers()
        trade_team_names = []
        for team in teams:
            team_object = users[str(team)]
            team_name, _ = self.parse_team_object(team_object)
            fields.append(self.discord.create_field(f"> {team_name}", ""))
            gives, gets = self.parse_trade_for_team(transaction, team)
            fields.append(self.discord.create_field("Gives ➡️️", "\n".join(gives), True))
            fields.append(self.discord.create_field("", "", True))
            fields.append(self.discord.create_field("Gets ⬅️", "\n".join(gets), True))
            trade_team_names.append(users[str(team)]['display_name'])

        return await self.discord.post_trade(trade_team_names, fields)
