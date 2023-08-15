from commissioner_bot.network import send_request_with_retries

add_string = "ADD ✅"
drop_string = "DROP 🔻"


class Discord:
    def __init__(self, waiver_webhook_url: str, trade_webhook_url: str, free_agency_webhook_url: str, username: str, user_url: str):
        self.waiver_webhook_url = waiver_webhook_url
        self.trade_webhook_url = trade_webhook_url
        self.free_agency_webhook_url = free_agency_webhook_url
        self.username = username
        self.user_url = user_url

    @staticmethod
    def create_field(name: str, value: str, inline: bool = False):
        return {
            "name": name,
            "value": value,
            "inline": inline
        }

    def post_free_agency_transaction(self, team_name: str, avatar_url: str, thumbnail_url: str, team_color: str, fields: list, add: bool):
        """
         Post a free agency transaction to Discord.
        :param team_name: String of the team that is making the transaction.
        :param avatar_url: Avatar URL of the team that is making the transaction.
        :param thumbnail_url: Thumbnail URL of the player that is being added.
        :param team_color: Color of the team that is making the transaction.
        :param fields: Array of fields to add to the message.
        :param add: Is this an add or just a drop?
        :return:
        """
        discord_message = {
            "username": self.username,
            "avatar_url": self.user_url,
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

        return self.send_discord_message(discord_message, self.free_agency_webhook_url)

    def post_waiver_claim_transaction(self, team_name: str, avatar_url: str, thumbnail_url: str, team_color: str, fields: list):
        """
        :param team_name: Name of the team that is making the waiver claim.
        :param avatar_url: URL of the avatar of the team that is making the waiver claim.
        :param thumbnail_url: URL of the thumbnail of the player that is being claimed.
        :param team_color: Color of the team that the player belongs to.
        :param fields: Array of fields to add to the message.
        :return:
        """

        discord_message = {
            "username": self.username,
            "avatar_url": self.user_url,
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

        return self.send_discord_message(discord_message, self.waiver_webhook_url)

    def post_trade(self, teams: list, fields: list):
        """
        Post a trade to Discord.
        :param teams: Array of team names that are involved in the trade.
        :param fields: Array of fields to add to the message.
        :return:
        """
        discord_message = {
            "username": self.username,
            "avatar_url": self.user_url,
            "embeds": [
                {
                    "author": {
                        "name": "Trade",
                        "icon_url": "https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw"
                    },
                    "title": " ↔️ ".join([team for team in teams]),
                    "fields": fields,
                    "thumbnail": {
                        "url": "https://www.theshirtlist.com/wp-content/uploads/2022/11/Epic-Handshake.jpg"
                    }
                }
            ]
        }

        return self.send_discord_message(discord_message, self.trade_webhook_url)

    @staticmethod
    def send_discord_message(message: dict, url: str):
        """
        Send a message to Discord.
        :param message: Message to send to Discord.
        :param url: Webhook URL to send the message to.
        """

        #TODO - Investigate 429 error for Too Many Requests

        return send_request_with_retries(url, method='POST', json_body=message)
