import discord
from discord.ext import commands
from commissioner_bot.environment import GUILD

add_string = "ADD ✅"
drop_string = "DROP 🔻"
poll_options = ["✅", "❌"]


class Discord:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def create_field(name: str, value: str, inline: bool = False):
        return {
            "name": name,
            "value": value,
            "inline": inline
        }

    async def post_free_agency_transaction(self, team_name: str, avatar_url: str, thumbnail_url: str, team_color: str, fields: list, add: bool):
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

        embedded_message = discord.Embed(title=team_name,  color=int(team_color, 16) if team_color else None)
        for field in fields:
            embedded_message.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        embedded_message.set_thumbnail(url=thumbnail_url)
        embedded_message.set_author(name="Free Agency Pickup" if add else "Drop", icon_url=avatar_url)
        guild = discord.utils.get(self.bot.guilds, name=GUILD)
        if guild is not None:
            print(guild.channels)
            channel_id = None
            for channel in guild.channels:
                if channel.name == "general":
                    channel_id = channel.id
                    break
            if channel_id is not None:
                target_channel = guild.get_channel(channel_id)
                if target_channel is not None:
                    await target_channel.send(embed=embedded_message)

        return True

    async def post_waiver_claim_transaction(self, team_name: str, avatar_url: str, thumbnail_url: str, team_color: str, fields: list):
        """
        :param team_name: Name of the team that is making the waiver claim.
        :param avatar_url: URL of the avatar of the team that is making the waiver claim.
        :param thumbnail_url: URL of the thumbnail of the player that is being claimed.
        :param team_color: Color of the team that the player belongs to.
        :param fields: Array of fields to add to the message.
        :return:
        """

        embedded_message = discord.Embed(title=team_name, color=int(team_color, 16) if team_color else None)
        for field in fields:
            embedded_message.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        embedded_message.set_thumbnail(url=thumbnail_url)
        embedded_message.set_author(name="Waiver Claim", icon_url=avatar_url)
        guild = discord.utils.get(self.bot.guilds, name=GUILD)
        if guild is not None:
            print(guild.channels)
            channel_id = None
            for channel in guild.channels:
                if channel.name == "general":
                    channel_id = channel.id
                    break
            if channel_id is not None:
                target_channel = guild.get_channel(channel_id)
                if target_channel is not None:
                    await target_channel.send(embed=embedded_message)

        return True

    async def post_trade(self, teams: list, fields: list):
        """
        Post a trade to Discord.
        :param teams: Array of team names that are involved in the trade.
        :param fields: Array of fields to add to the message.
        :return:
        """

        embedded_message = discord.Embed(title=" ↔️ ".join([team for team in teams]))
        for field in fields:
            embedded_message.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        embedded_message.set_author(name="Trade", icon_url="https://play-lh.googleusercontent.com/Ox2yWLWnOTu8x2ZWVQuuf0VqK_27kEqDMnI91fO6-1HHkvZ24wTYCZRbVZfRdx3DXn4=w240-h480-rw")
        embedded_message.set_thumbnail(url="https://www.theshirtlist.com/wp-content/uploads/2022/11/Epic-Handshake.jpg")
        embedded_message.set_footer(text="React with ✅ to approve the trade or ❌ to veto the trade.")
        guild = discord.utils.get(self.bot.guilds, name=GUILD)
        if guild is not None:
            print(guild.channels)
            channel_id = None
            for channel in guild.channels:
                if channel.name == "general":
                    channel_id = channel.id
                    break
            if channel_id is not None:
                target_channel = guild.get_channel(channel_id)
                if target_channel is not None:
                    poll_message = await target_channel.send(embed=embedded_message)

                    # Add the reactions
                    for emoji in poll_options:
                        await poll_message.add_reaction(emoji)

        return True
