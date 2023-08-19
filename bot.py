import os
import discord

from commissioner_bot.mongodb import MongoDatabase, MongoCollection

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
league_id = os.environ['LEAGUE_ID']
options = ["✅", "❌"]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)

db = MongoDatabase(os.environ['MONGODB_CONNECTION_URL'], 'commissioner_bot')
reaction_collection = MongoCollection(db, 'reactions')


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)
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
                # Send the message
                poll_embed = discord.Embed(title='Do you want to veto the trade between members?')
                poll_embed.set_footer(text=f"Remember vetos should only be used for collusion.")
                poll_message = await target_channel.send(embed=poll_embed)

                # Add the reactions
                for emoji in options:
                    await poll_message.add_reaction(emoji)


@client.event
async def on_message(message):
    if message.author == client.user:
        return message.content


@client.event
async def on_reaction_add(reaction, user):
    print(reaction, user)
    # Ignore if the reaction is added by a bot or a message created by a user
    if user.bot or reaction.message.author.bot is False:
        return

    # Check if the reaction is on a poll message
    message_id = reaction.message.id
    guild_id = reaction.message.guild.id
    reaction_collection.insert({
        'guild_id': guild_id,
        'message_id': message_id,
        'user_id': user.id,
        'reaction': reaction.emoji
    })
    reactions = reaction_collection.get_all({
        'guild_id': guild_id,
        'message_id': message_id,
        'user_id': user.id
    })
    if len(reactions) > 1:
        for item in reactions:
            if item['reaction'] != reaction.emoji:
                await reaction.message.remove_reaction(item['reaction'], user)
                reaction_collection.delete({
                    'guild_id': guild_id,
                    'message_id': message_id,
                    'user_id': user.id,
                    'reaction': item['reaction']
                })


client.run(TOKEN)
