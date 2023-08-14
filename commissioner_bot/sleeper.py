from commissioner_bot.network import send_request_with_retries
from commissioner_bot.webhook import post_free_agency_transaction, post_trade, post_waiver_claim_transaction
from commissioner_bot.utility import write_json_data
from commissioner_bot.mongodb import MongoDatabase
import os


class Sleeper:
    def __init__(self, league_id):
        self.league_id = league_id
        self.db = MongoDatabase(os.environ['MONGODB_CONNECTION_URL'], 'commissioner_bot', league_id)

    @staticmethod
    def get_nfl_state():
        return send_request_with_retries('https://api.sleeper.app/v1/state/nfl')

    @staticmethod
    def get_nfl_players():
        return send_request_with_retries('https://api.sleeper.app/v1/players/nfl')

    def get_league_users(self):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/users')

    def get_league_transactions(self, week):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/transactions/{week}')

    def get_league_rosters(self):
        return send_request_with_retries(f'https://api.sleeper.app/v1/league/{self.league_id}/rosters')

    def update_league_users(self):
        users = self.get_league_users()
        rosters = self.get_league_rosters()
        updated_users = {}
        for user in users:
            # Find the roster associated with the user
            for roster in rosters:
                if roster['owner_id'] == user['user_id']:
                    team_id = roster['roster_id']
                    updated_users[team_id] = {
                        'team_name': user['metadata'].get('team_name', None),
                        'avatar': user['metadata'].get('avatar', None),
                        'display_name': user.get('display_name', None)
                    }
                    break

        write_json_data('commissioner_bot/json/users.json', updated_users)

    def process_transactions(self, week):
        success, transactions = self.get_league_transactions(week)
        for transaction in transactions:
            transaction_id = transaction['transaction_id']

            # Check to see if the transaction has already been processed
            db_transactions = self.db.get_transaction(transaction_id)
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
                success, _ = post_waiver_claim_transaction(transaction, failed)
            elif transaction['type'] == 'trade':
                success, _ = post_trade(transaction)
            elif transaction['type'] == 'free_agent':
                success, _ = post_free_agency_transaction(transaction)
            if success:
                self.db.insert_transaction({"transaction_id": transaction_id, "status": "processed", "league_id": self.league_id})
