from commissioner_bot.network import send_request_with_retries


def get_nfl_state():
    return send_request_with_retries('GET', 'https://api.sleeper.app/v1/state/nfl')


def get_league_users(league_id):
    return send_request_with_retries('GET', f'https://api.sleeper.app/v1/league/{league_id}/users')


def get_league_transactions(league_id, week):
    return send_request_with_retries('GET', f'https://api.sleeper.app/v1/league/{league_id}/transactions/{week}')


def get_nfl_players():
    return send_request_with_retries('GET', 'https://api.sleeper.app/v1/players/nfl')


